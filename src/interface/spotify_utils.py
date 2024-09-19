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
import json
from spotipy.oauth2 import SpotifyOAuth

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
SPOTIPY_CLIENT_ID = config['spotify']['client_id']
SPOTIPY_CLIENT_SECRET = config['spotify']['client_secret']
SPOTIPY_REDIRECT_URI = config['spotify']['redirect_uri']

class SpotifyAPI:
    def __init__(self):
        """
        Initializes a new instance of the SpotifyAPI class.
        """
        # TODO: Double check scope - this is from a different project
        self.scope = "user-read-currently-playing user-library-read user-read-recently-played user-read-playback-state user-modify-playback-state playlist-read-private playlist-read-collaborative"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=self.scope))

    def refresh_token(self):
        """
        Refreshes the access token if it has expired.
        """
        token_info = self.sp.auth_manager.get_cached_token()
        if token_info != None:
            try:
                token_info = self.sp.auth_manager.refresh_access_token(token_info['refresh_token'])
            except requests.exceptions.ConnectionError:
                print(Fore.RED + "Error: Could not connect to Spotify API. Please check your internet connection." + Style.RESET_ALL)
                sys.exit(1)
        else:
            token_info = self.sp.auth_manager.get_access_token()
            #self.sp.auth_manager.cache_token(token_info, os.path.join(os.path.dirname(__file__), '..', 'data', 'spotify_token.json')) # Without specifying the cache path, the token is saved to the default cache path
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                    client_secret=SPOTIPY_CLIENT_SECRET,
                                                    redirect_uri=SPOTIPY_REDIRECT_URI,
                                                    scope=self.scope,
                                                    cache_path=os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'spotify_token.json')))
        


# Singleton instance of the SpotifyAPI class (for global use)
sp = SpotifyAPI()
sp.refresh_token()


