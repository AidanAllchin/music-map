#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
This handles SpotifyAPI authentication and requests.
Saves the access token to a file for future use.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
import requests
import spotipy
from datetime import datetime
import time
import webbrowser
import threading
from flask import Flask, redirect, request # type: ignore
import json
from spotipy.oauth2 import SpotifyOAuth

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
debug = config['settings']['debug']

if not debug:
    SPOTIPY_CLIENT_ID = config['spotify']['client_id']
    SPOTIPY_CLIENT_SECRET = config['spotify']['client_secret']
else:
    SPOTIPY_CLIENT_ID = input("Client ID: ")
    SPOTIPY_CLIENT_SECRET = input("Client Secret: ")

SPOTIPY_REDIRECT_URI = config['spotify']['redirect_uri']
SPOTIPY_REDIRECT_PORT= SPOTIPY_REDIRECT_URI.split(':')[-1].split('/')[0]
CACHE_PATH = config['paths']['spotify_token_path']
CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', '..') + CACHE_PATH

# Using Flask to handle the authentication
app = Flask(__name__)
app.secret_key = os.urandom(24)

class SpotifyAPI:
    def __init__(self):
        """
        Initializes a new instance of the SpotifyAPI class.
        """
        self.scope = "user-library-read playlist-read-private playlist-read-collaborative"
        self.sp = None
        self.auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID, 
            client_secret=SPOTIPY_CLIENT_SECRET, 
            redirect_uri=SPOTIPY_REDIRECT_URI, 
            scope=self.scope,
            show_dialog=True,
            cache_path=CACHE_PATH
        )
        print(f"{Style.BRIGHT}[SpotifyAPI]: {Style.NORMAL}{Fore.GREEN}SpotifyAPI initialized.{Style.RESET_ALL}")

    def authenticate(self):
        @app.route('/')
        def index():
            return redirect(self.auth_manager.get_authorize_url())
        
        @app.route('/callback')
        def callback():
            if request.args.get('code'):
                self.auth_manager.get_access_token(request.args['code'], as_dict=False)
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                return "Authentication successful. You can now close this tab."
            else:
                return "Error: Authentication failed."
            
        print(f"{Style.BRIGHT}[SpotifyAPI]: {Style.NORMAL}{Fore.GREEN}Please authenticate with Spotify by visiting the following link:{Style.RESET_ALL}")
        webbrowser.open_new_tab(f'{SPOTIPY_REDIRECT_URI.split("/callback")[0]}')
        threading.Thread(target=lambda: app.run(port=SPOTIPY_REDIRECT_PORT)).start()

    def refresh_token(self):
        """
        Refreshes the access token if it has expired.
        """
        if self.sp:
            token = self.auth_manager.get_cached_token()['refresh_token']
            self.auth_manager.refresh_access_token(token)
        else:
            self.authenticate()
            self.refresh_token()
    
    def load_playlist_to_tsv(self, playlist_uri: str, tsv_path: str):
        """
        Loads a Spotify playlist to a TSV file.

        Args:
            playlist_url (str): URL of the Spotify playlist.
            tsv_path (str): Path to the TSV file.
        """
        if not playlist_uri.startswith('spotify:playlist:'):
            playlist_uri = self.get_playlist_uri_for_name(playlist_uri)
            if playlist_uri == None:
                print(f"{Style.BRIGHT}[SpotifyAPI]: {Style.NORMAL}{Fore.RED}Error: Could not find playlist with name '{playlist_uri_or_name}'.{Style.RESET_ALL}")
                sys.exit(1)
        playlist_id = playlist_uri.split(':')[-1]
        try:
            playlist = self.sp.playlist(playlist_id)
        except spotipy.SpotifyException:
            print(f"{Style.BRIGHT}[SpotifyAPI]: {Style.NORMAL}{Fore.RED}Error: Could not load playlist. Please check the playlist URL.{Style.RESET_ALL}")
            sys.exit(1)

        with open(tsv_path, 'w') as f:
            f.write("Track ID\tTrack Name\tTrack Url\tArtists\tAlbum\tSong Length (s)\tMetrics\n")
            for track in playlist['tracks']['items']:
                track_id = track['track']['id']
                metrics = self.get_spotify_metrics(track_id)
                track_name = track['track']['name']
                track_url = track['track']['external_urls']['spotify']
                artists = ', '.join([artist['name'] for artist in track['track']['artists']])
                album = track['track']['album']['name']
                song_length = track['track']['duration_ms'] / 1000
                f.write(f"{track_id}\t{track_name}\t{track_url}\t{artists}\t{album}\t{song_length}\t{json.dumps(metrics)}\n")
        print(f"{Style.BRIGHT}{Fore.GREEN}[SpotifyAPI]: Playlist saved to {tsv_path.replace(os.path.join(os.path.dirname(__file__), '..', '..'), '')}{Style.RESET_ALL}\n")

    def get_playlists(self):
        """
        Retrieves the playlists for the user's Spotify account.

        Returns:
            playlists (list): A list of dictionaries containing information about the user's playlists.
                Each dictionary contains the following keys:
                - 'name': The name of the playlist.
                - 'id': The ID of the playlist.
                - 'owner': The owner of the playlist.
        """
        playlists = self.sp.current_user_playlists()
        playlist_dict = []
        while playlists:
            for playlist in playlists['items']:
                playlist_dict.append({
                    'name': playlist['name'],
                    'id': playlist['id'],
                    'owner': playlist['owner']['display_name'],
                    'uri': playlist['uri'],
                    'tracks': playlist['tracks']['total']
                })
            if playlists['next']:
                playlists = self.sp.next(playlists)
            else:
                playlists = None
        return playlist_dict

    def get_playlist_uri_for_name(self, playlist_name):
        """
        Retrieves the URI of a playlist by its name.

        Args:
            playlist_name (str): The name of the playlist to retrieve.

        Returns:
            str: The URI of the playlist.
        """
        playlists = self.get_playlists()
        for playlist in playlists:
            if playlist['name'].lower() == playlist_name.lower():
                return playlist['uri']
        return None

    def get_song_analysis(self, song_id: str) -> dict:
        """
        Retrieves the analysis of a song from Spotify.

        Args:
            song_id (str): The ID of the song.

        Returns:
            dict: A dictionary containing the analysis of the song.
        """
        analysis = self.sp.audio_analysis(song_id)
        return analysis

    def get_spotify_metrics(self, song_id: str) -> dict:
        """
        Retrieves metrics for a song from Spotify.

        Args:
            song_id (str): The ID of the song.

        Returns:
            dict: A dictionary containing metrics for the song.
        """
        metrics = self.sp.audio_features(song_id)[0]
        metrics.pop('type')
        metrics.pop('id')
        metrics.pop('uri')
        metrics.pop('track_href')
        metrics.pop('analysis_url')
        metrics.pop('duration_ms')
        return metrics

    def get_user_saved_tracks(self):
        """
        Retrieves the user's saved tracks (liked songs) with their added dates.

        Returns:
            list: A list of dictionaries containing information about the user's saved tracks.
                Each dictionary contains the following keys:
                - 'track_id': The ID of the track.
                - 'track_name': The name of the track.
                - 'track_url': The Spotify URL of the track.
                - 'artists': The artists of the track.
                - 'album': The album of the track.
                - 'song_length': The length of the track in seconds.
                - 'added_at': The date and time the track was saved.
        """
        results = self.sp.current_user_saved_tracks()
        tracks = []
        while results:
            for item in results['items']:
                track = item['track']
                tracks.append({
                    'track_id': track['id'],
                    'track_name': track['name'],
                    'track_url': track['external_urls']['spotify'],
                    'artists': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'song_length': track['duration_ms'] / 1000,
                    'added_at': item['added_at']  # This is the timestamp we're interested in
                })
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        print(f"{Style.NORMAL}[SpotifyAPI]: {Style.DIM}{Fore.LIGHTGREEN_EX}Retrieved {len(tracks)} liked songs.{Style.RESET_ALL}")
        return tracks
    
    def load_likes_to_tsv(self):
        """
        Loads the user's liked songs to a TSV file.
        """
        print(f"{Style.BRIGHT}[SpotifyAPI]: {Style.NORMAL}{Fore.CYAN}Saving liked songs to TSV...{Style.RESET_ALL}", end='\r', flush=True)
        tsv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', 'likes.tsv')
        tracks = self.get_user_saved_tracks()
        with open(tsv_path, 'w') as f:
            f.write("Track ID\tTrack Name\tTrack Url\tArtists\tAlbum\tSong Length (s)\tMetrics\tAdded At\n")
            for track in tracks:
                f.write(f"{track['track_id']}\t{track['track_name']}\t{track['track_url']}\t{track['artists']}\t{track['album']}\t{track['song_length']}\t{json.dumps(self.get_spotify_metrics(track['track_id']))}\t{track['added_at']}\n")
        print(f"\n{Style.BRIGHT}{Fore.GREEN}[SpotifyAPI]: Liked songs saved to {tsv_path.replace(os.path.join(os.path.dirname(__file__), '..', '..'), '')}{Style.RESET_ALL}\n")

# Singleton instance of the SpotifyAPI class (for global use)
sp = SpotifyAPI()
#sp.refresh_token()
#sp.authenticate()

if __name__ == "__main__":
    sp.authenticate()
    while sp.sp is None:
        print(f"{Style.BRIGHT}[SpotifyAPI]: {Style.NORMAL}{Fore.RED}Error: SpotifyAPI not authenticated. Please authenticate first.{Style.RESET_ALL}", end='\r', flush=True)
        time.sleep(1)
    
    #plist = "Driving Through Clouds"
    #tsv = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', f'{plist.lower().replace(' ', '_')}.tsv')
    # sp.load_playlist_to_tsv(plist, tsv)

    # Testing with official Spotify playlists instead of user playlists
    if not os.path.exists(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', 'spotify_official_genre_mappings')):
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', 'spotify_official_genre_mappings'))
    # get date_str as DD_MM_YYYY
    date_str = datetime.now().strftime("%d_%m_%Y")
    country_playlists = [
        {'name': 'Hot Country', 'uri': 'spotify:playlist:37i9dQZF1DX1lVhptIYRda', 'path': f'hot_country_{date_str}'},
        {'name': 'All New Country', 'uri': 'spotify:playlist:37i9dQZF1DWVn8zvR5ROMB', 'path': f'all_new_country_{date_str}'},
        {'name': 'Cozy Country', 'uri': 'spotify:playlist:37i9dQZF1DX1hFALgilvpL', 'path': f'cozy_country_{date_str}'},
        {'name': 'Country Tailgate', 'uri': 'spotify:playlist:37i9dQZF1DX3ph0alWhOXm', 'path': f'country_tailgate_{date_str}'},
        {'name': 'Breakout Country', 'uri': 'spotify:playlist:37i9dQZF1DWW7RgkOJG32Y', 'path': f'breakout_country_{date_str}'},
        {'name': 'sad girl country', 'uri': 'spotify:playlist:37i9dQZF1DWU4lunzhQdRx', 'path': f'sad_girl_country_{date_str}'}
    ]

    if not os.path.exists(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', 'spotify_official_genre_mappings', 'country')):
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', 'spotify_official_genre_mappings', 'country'))
    for playlist in country_playlists:
        tsv = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', 'spotify_official_genre_mappings', 'country', f'{playlist["path"]}.tsv')
        sp.load_playlist_to_tsv(playlist['uri'], tsv)

    # test_song_id = '4DwQLjh6eCUHX8Ri4ZpG8v'
    # print(sp.get_spotify_metrics(test_song_id))
    # print(sp.get_song_analysis(test_song_id))
    
    #sp.load_likes_to_tsv()
