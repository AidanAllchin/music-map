#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Organizes, downloads, and checks the waveforms of songs from YouTube.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
import time
import json
import asyncio
from typing import Tuple
import yt_dlp
import contextlib
import subprocess
from src.utils.log_suppression import SuppressLogger

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
debug = config['settings']['debug']

AUDIO_DEST_PATH = os.path.join(os.path.dirname(__file__), "..", "..") + config['paths']['audio_destination_path']

async def find_best_link(search_query: str, target_length: float, threshold: int) -> str:
    ydl_opts = {
        'quiet': True,
        'default_search': 'ytsearch10',  # Search and return top 10 results
        'skip_download': True,          # Don't download anything
        'extract_flat': 'in_playlist',  # Only get metadata
    }
    search_query = search_query.replace(':', '-')

    # Asynchronous for use in the batching
    async def extract_info_async(ydl_opts, search_query):
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
    
    # Extract the metadata
    results = await extract_info_async(ydl_opts, search_query)

    video_lengths = []
    video_urls    = []
    
    # Extract the video lengths and URLs
    if 'entries' in results:
        for entry in results['entries']:
            video_lengths.append(entry['duration'])
            video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
    
    # Find the video with the closest length to the target length
    best_length = None
    best_url = None
    best_diff = float('inf')
    for length, url in zip(video_lengths, video_urls):
        if length is None:
            continue
        length = float(length)
        diff = abs(length - target_length)

        # Update the best video if the current one is closer
        if diff < best_diff:
            best_diff = diff
            best_length = length
            best_url = url

    if debug:
        print(f"{Style.DIM}[ytdlp]: Target: {target_length}, Best: {best_length}, Diff: {round(best_diff, 3)}{Style.RESET_ALL}")

    if best_diff < threshold:
        #print(f"Best URL: {best_url}")
        return best_url
    else:
        print(f"{Fore.RED}[ytdlp]: {Style.DIM}No video found within threshold.{Style.RESET_ALL}")
        return None
    
async def download_one_by_url(sp_id: int, url: str):
    p = os.path.join(AUDIO_DEST_PATH, f"sp_id_{sp_id}")
    # print(p)
    if os.path.exists(p + ".mp3"):
        print(f"{Fore.RED}[ytdlp]: {Style.DIM}File already exists: {p}{Style.RESET_ALL}")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cachedir': False,
        'quiet': True,
        # Save the file as to_embed.mp3
        'outtmpl': p,
        "logger": SuppressLogger() if not debug else None
    }

    async def download_youtube_audio(u: str = url):
        subprocess.run(['sudo', 'rm', '-rf', '~/.cache/yt-dlp'], check=True)
        loop = asyncio.get_event_loop()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for attempt in range(5):
                try:
                    if debug:
                        print(f"{Fore.LIGHTBLUE_EX}[ytdlp]: {Style.DIM}Attempting download of {u} to {p}.mp3...{Style.RESET_ALL}")
                    await loop.run_in_executor(None, lambda: ydl.download([u]))
                    break
                except yt_dlp.DownloadError as e:
                    print(f"{Fore.RED}[ytdlp]: {Style.DIM}Download failed. Retrying...{Style.RESET_ALL}")
                    time.sleep(5)
                    if attempt == 4:
                        print(f"{Fore.RED}[ytdlp]: {Style.DIM}Download failed after 5 attempts.{Style.RESET_ALL}")
                        raise e

    # Supress all output from the below function
    if not debug:
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            sys.stdout = f
            await download_youtube_audio()
        sys.stdout = sys.__stdout__
    else:
        await download_youtube_audio()
    
async def download_best(search_query: str, target_length: float, threshold: int, sp_id: int = None) -> Tuple[bool, str]:
    """
    Downloads the best matching video based on the search query and target length.

    Args:
        search_query (str): The search query to find the video.
        target_length (float): The target length of the video in seconds.
        threshold (int): The acceptable deviation from the target length in seconds.

    Returns:
        tuple: A tuple containing:
            - bool: True if a video was found and downloaded, False otherwise.
            - str: The path to the downloaded video.
    """
    url = await find_best_link(search_query, target_length, threshold)

    if sp_id is None:
        sp_id = input("Enter the Spotify ID: ")

    if url is not None:
        await download_one_by_url(sp_id, url)
        #path = os.path.join(AUDIO_DEST_PATH, f"yt_id_{url.split('=')[-1]}.mp3")
        path = os.path.join(AUDIO_DEST_PATH, f"sp_id_{sp_id}.mp3")
        #convert_to_wav(path)
        return True, path#path[:-4] + '.wav'
    else:
        return False, None
    
def convert_to_wav(file: str):
    """
    Converts an audio file to WAV format.

    Args:
        file (str): The path to the audio file.

    Returns:
        str: The path to the converted WAV file.
    """
    wav_file = file.replace('.mp3', '.wav')
    os.system(f"ffmpeg -i {file} -acodec pcm_s16le -ac 1 -ar 16000 {wav_file}")
    return wav_file

if __name__ == "__main__":
    # Tests
    asyncio.run(download_best("Awaken - Alternate Version by Alex Baker", 393.333, 5, "3pLlcz1uuEqas5TkVzGiRe"))