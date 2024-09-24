#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
This script is used to download the VGGish model files and create the necessary directories.
"""

import os, sys, subprocess, json

# Install the required packages
if not os.path.exists("requirements.txt"):
    print("Error: requirements.txt not found.")
    sys.exit(1)

subprocess.run(["pip", "install", "-r", "requirements.txt"])

from colorama import Fore, Style

def ensure_directory_exists(dir: str):
    """
    Ensures that the specified directory exists.
    Args:
        dir (str): The directory to check.
    """
    try:
        os.makedirs(dir, exist_ok=True)
        print(f"{Fore.GREEN}[init]: Created directory: {dir}{Style.RESET_ALL}")
    except PermissionError:
        print(f"{Fore.RED}[init]: {Style.DIM}Permission denied when creating directory: {dir}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[init]: Attempting to create directory with sudo...{Style.RESET_ALL}")
        try:
            subprocess.run(['sudo', 'mkdir', '-p', dir], check=True)
            subprocess.run(['sudo', 'chmod', '777', dir], check=True)
            print(f"{Fore.GREEN}[init]: Successfully created directory with sudo.{Style.RESET_ALL}")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}[init]: Failed to create directory even with sudo: {e}{Style.RESET_ALL}")
            raise

# Create directories
if not os.path.exists("data"):
    ensure_directory_exists("data")
    ensure_directory_exists("data/vggish_model")
    ensure_directory_exists("data/waveforms")
    ensure_directory_exists("data/embeddings")
    ensure_directory_exists("data/playlists")
elif not os.path.exists("data/vggish_model"):
    ensure_directory_exists("data/vggish_model")
elif not os.path.exists("data/waveforms"):
    ensure_directory_exists("data/waveforms")
elif not os.path.exists("data/embeddings"):
    ensure_directory_exists("data/embeddings")
elif not os.path.exists("data/playlists"):
    ensure_directory_exists("data/playlists")

# Download the VGGish model files (WIP)
if not os.path.exists("data/vggish_model/vggish_model.ckpt") or not os.path.exists("data/vggish_model/vggish_pca_params.npz"):
    sys_type = sys.platform
    if sys_type == "linux":
        subprocess.run(["wget", "https://storage.googleapis.com/audioset/vggish_model.ckpt", "-O", "data/vggish_model/vggish_model.ckpt"])
        subprocess.run(["wget", "https://storage.googleapis.com/audioset/vggish_pca_params.npz", "-O", "data/vggish_model/vggish_pca_params.npz"])
    elif sys_type == "win32":
        subprocess.run(["wget", "https://storage.googleapis.com/audioset/vggish_model.ckpt", "-O", "data/vggish_model/vggish_model.ckpt"])
        subprocess.run(["wget", "https://storage.googleapis.com/audioset/vggish_pca_params.npz", "-O", "data/vggish_model/vggish_pca_params.npz"])
    # mac doesn't have wget
    elif sys_type == "darwin":
        subprocess.run(["curl", "https://storage.googleapis.com/audioset/vggish_model.ckpt", "-o", "data/vggish_model/vggish_model.ckpt"])
        subprocess.run(["curl", "https://storage.googleapis.com/audioset/vggish_pca_params.npz", "-o", "data/vggish_model/vggish_pca_params.npz"])
else:
    print("VGGish model files already downloaded.")

# Set up SpotifyAPI
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
if config['spotify']['client_id'] == "" or config['spotify']['client_secret'] == "":
    print("Please set up your SpotifyAPI credentials:")
    client_id = input("Client ID: ")
    client_secret = input("Client Secret: ")
    config['spotify']['client_id'] = client_id
    config['spotify']['client_secret'] = client_secret
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    print("SpotifyAPI credentials saved.")
else:
    print("SpotifyAPI credentials already set up.")

print("Setup complete.")