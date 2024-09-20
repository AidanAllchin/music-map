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

# Create directories
if not os.path.exists("data"):
    os.makedirs("data")
    os.makedirs("data/vggish_model")
    os.makedirs("data/waveforms")
    os.makedirs("data/embeddings")
elif not os.path.exists("data/vggish_model"):
    os.makedirs("data/vggish_model")
elif not os.path.exists("data/waveforms"):
    os.makedirs("data/waveforms")
elif not os.path.exists("data/embeddings"):
    os.makedirs("data/embeddings")

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