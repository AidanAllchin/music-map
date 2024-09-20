#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Run this script to start the application.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
from src.interface.spotify_utils import sp
from src.embeddings.generator import add_embeddings_to_tsv
from src.embeddings.vgg_maxpool import extract_one_embedding

def get_playlist_embedding(playlist_name: str):
    """
    Extracts the embedding for a playlist.
    """
    # Get the playlist ID
    playlist_id = sp.get_playlist_uri_for_name(playlist_name)

    # Get the track IDs
    tsv_path = os.path.join(os.path.dirname(__file__), 'data', 'playlists', f'{playlist_name.lower().replace(' ', '_')}.tsv')
    sp.load_playlist_to_tsv(playlist_id, tsv_path)

    # Add the embeddings to the TSV
    add_embeddings_to_tsv(tsv_path)


def main():
    """
    Main function.
    """
    print(f"{Style.BRIGHT}[Main]: {Style.NORMAL}{Fore.GREEN}Starting the application...{Style.RESET_ALL}")

    # Get the playlist name
    playlist_name = input("Enter the name of the playlist: ")

    # Extract the embedding for the playlist
    get_playlist_embedding(playlist_name)

    print(f"{Style.BRIGHT}[Main]: {Style.NORMAL}{Fore.GREEN}Application finished.{Style.RESET_ALL}")
