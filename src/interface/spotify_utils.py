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
            f.write("Track ID\tTrack Name\tTrack Url\tArtists\tAlbum\tSong Length (s)\n")
            for track in playlist['tracks']['items']:
                track_id = track['track']['id']
                track_name = track['track']['name']
                track_url = track['track']['external_urls']['spotify']
                artists = ', '.join([artist['name'] for artist in track['track']['artists']])
                album = track['track']['album']['name']
                song_length = track['track']['duration_ms'] / 1000
                f.write(f"{track_id}\t{track_name}\t{track_url}\t{artists}\t{album}\t{song_length}\n")
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


# Singleton instance of the SpotifyAPI class (for global use)
sp = SpotifyAPI()
#sp.refresh_token()
#sp.authenticate()

if __name__ == "__main__":
    plist = "Driving Through Clouds"
    tsv = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'playlists', f'{plist.lower().replace(' ', '_')}.tsv')
    # sp.load_playlist_to_tsv(plist, tsv)

