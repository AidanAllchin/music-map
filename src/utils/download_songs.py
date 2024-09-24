#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Batch downloads songs from YouTube using yt-dlp and saves them.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
import asyncio
import os
import json
import pandas as pd
from typing import Tuple
from src.utils.ytdl_handler import find_best_link, download_one_by_url, download_best
import tqdm

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.json")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

AUDIO_DEST_PATH = os.path.join(os.path.dirname(__file__), "..", "..", config["paths"]["audio_destination_path"])
YT_LINKS_PATH   = os.path.join(os.path.dirname(__file__), "..", "..", config['paths']['yt_links_path'])

def search_for_existing_link(song_info):
    """
    Searches for an existing YouTube link for a given song in a TSV file.
    This function looks for a song matching the provided track name and artists
    in the 'yt_links_for_missing_songs.tsv' file. If a match is found, it returns
    the corresponding YouTube link.
    Args:
        song_info (dict): A dictionary containing the song information with keys:
            - "Track Name" (str): The name of the track.
            - "Artists" (str): The artists of the track.
    Returns:
        str or None: The YouTube link if a match is found, otherwise None.
    """

    if os.path.exists(YT_LINKS_PATH):
        df = pd.read_csv(YT_LINKS_PATH, sep="\t")
        tname = song_info["Track Name"]
        artists = song_info["Artists"]
        
        # Lookup the song in the DataFrame
        song = df[(df["Track Name"] == tname) & (df["Artists"] == artists)]

        if not song.empty:
            return song["YouTube Link"].values[0]
    return None

def write_url_to_tsv(song_id: int, url: str):
    """
    Writes a YouTube link to a TSV file.
    This function appends a new row to the 'yt_links_for_missing_songs.tsv' file
    with the provided song ID and YouTube link.

    Args:
        song_id (int): The song ID.
        url (str): The YouTube link.
    """
    # Check if the file exists
    if not os.path.exists(YT_LINKS_PATH):
        with open(YT_LINKS_PATH, "w") as f:
            f.write("Song ID\tYouTube Link\n")
    
    # Check the song ID doesn't already exist
    df = pd.read_csv(YT_LINKS_PATH, sep="\t")
    if song_id in df["Song ID"].values:
        if url != df[df["Song ID"] == song_id]["YouTube Link"].values[0]:
            print(f"Warning: Song ID {song_id} already exists with a different link.")
        return
    
    # Append the new row
    with open(YT_LINKS_PATH, "a") as f:
        f.write(f"{song_id}\t{url}\n")

async def download_song(song_info: pd.Series, id: int, pbar) -> Tuple[int, str]:
    """
    Asynchronously downloads a song based on provided song information.
    This function first checks if a link for the song already exists. If it 
    does, and the song has not been downloaded yet, it downloads the song 
    using the existing link. If no link is found, it searches for the best 
    link based on the song's track name and artists, and then downloads the 
    song if a suitable link is found.

    Args:
        song_info (pd.Series): A pandas Series containing information about the song, including 'Track Name', 'Artists', and 'Song Length (s)'.
        id (int): The Spotify id of the song.
        pbar: A progress bar object to update the download progress.
    
    Returns:
        tuple: A tuple containing the Spotify song ID and a boolean indicating whether the song was successfully downloaded.
    """
    link = search_for_existing_link(song_info)
    p = os.path.join(AUDIO_DEST_PATH, f"sp_id_{id}.mp3")

    if link is not None:
        if not os.path.exists(p):
            # Song hasn't been downloaded yet but we have a link for it
            await download_one_by_url(id, link)
            pbar.update(1)
            write_url_to_tsv(id, link)
        else:
            #print(f"Skipping download for {id}, already exists.")
            pbar.update(1)
        return id, True

    # Otherwise, search for the best link
    search_query = f"{song_info['Track Name']} by {song_info['Artists']}"
    try:
        best_link = await find_best_link(
            search_query=search_query, 
            target_length=song_info["Song Length (s)"], 
            threshold=10
        )

    except Exception as e:
        print(f"Failed to find a link for {search_query}: {e}")
        best_link = None
        return id, False

    # If we find one, download it
    if best_link:
        # Check if the song already exists
        if not os.path.exists(AUDIO_DEST_PATH):
            await download_one_by_url(id, best_link)
            write_url_to_tsv(id, best_link)
        
        # otherwise skip because it's already downloaded
        pbar.update(1)
        return id, True
    else:
        print(f"Could not find a link for {search_query}.")
        return id, False

async def download_songs_batch(songs_batch, start_index: int, pbar):
    """
    Asynchronously downloads a batch of songs.

    Args:
        songs_batch (list): A list of songs to be downloaded.
        start_index (int): The starting index for the batch.
        pbar (tqdm.tqdm): A progress bar instance to update the download progress.

    Returns:
        list: A list of results from the download_song function for each song in the batch.
    """
    tasks = [download_song(song, start_index + i, pbar) for i, song in enumerate(songs_batch)]
    return await asyncio.gather(*tasks)

async def download_songs(frame: pd.DataFrame):
    """
    Asynchronously downloads songs based on information in the provided
    DataFrame. This function processes each song in the DataFrame concurrently,
    searching for the best link and downloading the song if a suitable link is 
    found. As each song is saved based on its Spotify ID, nothing needs to be
    returned.

    Args:
        frame (pd.DataFrame): DataFrame containing columns 'Track Name', 'Artists', 
                              'Song Length (s)', and the index as Spotify IDs.
    """
    async def process_song(row):
        spotify_id = row['Track ID']
        search_query = f"{row['Track Name']} by {row['Artists']}"
        success, file_path = await download_best(
            search_query=search_query,
            target_length=row['Song Length (s)'],
            threshold=5, # Allow a 5-second deviation from the target length
            sp_id=spotify_id
        )
        return success, file_path

    # Create a progress bar
    pbar = tqdm.tqdm(total=len(frame), desc="Downloading songs")

    # Process songs concurrently
    tasks = [process_song(row) for _, row in frame.iterrows()]
    results = await asyncio.gather(*tasks)

    # Update progress bar
    pbar.update(len(results))
    pbar.close()

    print(f"{Fore.GREEN}Finished downloading songs.{Style.RESET_ALL}")

# if __name__ == "__main__":
#     asyncio.run(download_songs())
