#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
This script is used to download the VGGish model files and create the necessary directories.
"""

import os, sys, subprocess, json

# Install the required packages
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
subprocess.run(["wget", "https://storage.googleapis.com/audioset/vggish_model.ckpt", "-O", "data/vggish_model/vggish_model.ckpt"])
subprocess.run(["wget", "https://storage.googleapis.com/audioset/vggish_pca_params.npz", "-O", "data/vggish_model/vggish_pca_params.npz"])

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