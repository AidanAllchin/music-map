#!/usr/bin/env python3

import os, sys, subprocess

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

print("Setup complete.")