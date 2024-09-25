#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Created on Tue Sep 24 2024

Downloads and processes the baseline data for the map.
This data is gathered from official Spotify genere-based playlists.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
import asyncio
import json
import pandas as pd
from datetime import datetime
from src.interface.spotify_utils import sp

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

debug = config['settings']['debug']
PLAYLISTS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', config['paths']['playlists_path'][1:], 'spotify_official_genre_mappings')
BASELINE_DATA = config['baseline_data']

def load_playlists() -> list:
    """
    Loads the playlists from the config file to the correct .tsv files.

    Returns:
        list: A list of the paths to the .tsv files.
    """
    date_str = datetime.now().strftime("%d_%m_%Y")

    for genre_dict in BASELINE_DATA:
        genre = genre_dict['genre']
        playlists = genre_dict['playlists']
        if not os.path.exists(os.path.join(PLAYLISTS_PATH, genre)):
            os.makedirs(os.path.join(PLAYLISTS_PATH, genre))

        for name, uri, p in playlists.items():

            path = os.path.join(PLAYLISTS_PATH, {genre}, f"{p}_{date_str}.tsv")
            sp.load_playlist_to_tsv(uri, path)

            print(f"{Style.BRIGHT}[BaselineData]: {Style.NORMAL}{Fore.MAGENTA}Loaded playlist {name} to {p}.{Style.RESET_ALL}")

if __name__ == "__main__":
    load_playlists()
    






