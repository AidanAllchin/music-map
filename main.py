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
import asyncio
import time
from src.interface.spotify_utils import sp
from src.embeddings.generator import add_embeddings_to_tsv, download_and_embed_tsv
#from src.embeddings.vgg_maxpool import extract_one_embedding

async def get_playlist_embedding(playlist_name: str):
    """
    Extracts the embedding for a playlist.
    """
    # Get the playlist ID
    playlist_id = sp.get_playlist_uri_for_name(playlist_name)

    # Get the track IDs
    tsv_path = os.path.join(os.path.dirname(__file__), 'data', 'playlists', f'{playlist_name.lower().replace(' ', '_')}.tsv')
    sp.load_playlist_to_tsv(playlist_id, tsv_path)

    # Add the embeddings to the TSV
    await download_and_embed_tsv(tsv_path)

async def get_likes_embedding():
    """
    Extracts the embedding for all liked songs.
    """
    # Get the liked songs
    sp.load_likes_to_tsv()

    likes_path = os.path.join(os.path.dirname(__file__), 'playlists', 'likes.tsv')

    # Add the embeddings to the TSV
    await download_and_embed_tsv(likes_path)

def menu():
    """
    Displays the main menu.
    """
    print(f"{Style.BRIGHT}\n[ Menu ]{Style.RESET_ALL}")
    print("1. Extract Embedding for Playlist")
    print("2. Extract Embeddings for All Liked Songs")
    print("0. Exit")
    choice = input("Enter your choice: ")

    if choice == '1':
        playlist_name = input("Enter the name of the playlist: ")
        asyncio.run(get_playlist_embedding(playlist_name))
    elif choice == '2':
        asyncio.run(get_likes_embedding())
    elif choice == '0':
        sys.exit(0)
    else:
        print(f"{Style.BRIGHT}\n[Main]: {Style.NORMAL}{Fore.RED}Invalid choice.{Style.RESET_ALL}")

def main():
    """
    Main function.
    """
    print(f"{Style.BRIGHT}[Main]: {Style.NORMAL}{Fore.GREEN}Starting the application...{Style.RESET_ALL}")

    # Authenticate the Spotify API
    sp.authenticate()

    while sp.sp is None:
        print(f"{Style.BRIGHT}[Main]: {Style.NORMAL}{Fore.YELLOW}Please authenticate the Spotify API...{Style.RESET_ALL}", end="\r", flush=True)
        time.sleep(1)

    # Get the playlist name
    # playlist_name = input("Enter the name of the playlist: ")

    # # Extract the embedding for the playlist
    # asyncio.run(get_playlist_embedding(playlist_name))

    while True:
        try:
            menu()
        except KeyboardInterrupt:
            print(f"{Style.BRIGHT}[Main]: {Style.NORMAL}{Fore.GREEN}Application finished.{Style.RESET_ALL}")
            sys.exit(0)

if __name__ == "__main__":
    main()