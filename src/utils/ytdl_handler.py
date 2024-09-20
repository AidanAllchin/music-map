#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Organizes, downloads, and checks the waveforms of songs from YouTube.
"""

import os, sys
from pathlib import Path
import time

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
from typing import Tuple
import yt_dlp
import contextlib

DESTINATION_PATH_WAVS = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'waveforms')

def find_best_length(search_query, target_length, threshold) -> str:
    ydl_opts = {
        'quiet': True,
        'default_search': 'ytsearch10',  # Search and return top 10 results
        'skip_download': True,          # Don't download anything
        'extract_flat': 'in_playlist',  # Only get metadata
    }
    search_query = search_query.replace(':', '-')

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(search_query, download=False)
    
    video_lengths = []
    video_urls    = []
    
    # Extract the video lengths and URLs
    if 'entries' in result:
        for entry in result['entries']:
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
        if diff < best_diff:
            best_diff = diff
            best_length = length
            best_url = url

    print(f"[ytdlp]: {Style.DIM} Target: {target_length}, Best: {best_length}, Diff: {best_diff}{Style.RESET_ALL}")

    if best_diff < threshold:
        #print(f"Best URL: {best_url}")
        return best_url
    else:
        print(f"[ytdlp]: {Style.DIM}No video found within threshold.{Style.RESET_ALL}")
        return None
    
def download_one_by_url(url):
    id = url.split('=')[-1]
    def download_youtube_audio(search_for: str):
        #subprocess.run(['sudo', 'rm', '-rf', '~/.cache/yt-dlp'], check=True)

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
            'outtmpl': os.path.join(DESTINATION_PATH_WAVS, f"yt_id_{id}.mp3")
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            retries = 0
            while retries < 5:
                try:
                    ydl.download([url])
                    break
                except yt_dlp.utils.DownloadError as e:
                    time.sleep(1)
                    retries += 1
                    print("Error downloading audio: " + str(e))
            
            if retries == 3:
                #print("Failed to download audio for: " + search_for)
                raise Exception("Failed to download audio for: " + search_for)

    # Supress all output from the below function
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
        sys.stdout = f
        download_youtube_audio(url)
    sys.stdout = sys.__stdout__
    
def download_best(search_query: str, target_length: float, threshold: int) -> Tuple[bool, str]:
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
    url = find_best_length(search_query, target_length, threshold)
    if url is not None:
        download_one_by_url(url)
        return True, os.path.join(DESTINATION_PATH_WAVS, f"yt_id_{url.split('=')[-1]}.mp3")
    else:
        return False, None