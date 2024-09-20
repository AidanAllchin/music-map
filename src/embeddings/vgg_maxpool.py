#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 2024

This script extracts audio embeddings from audio files using a pre-trained VGGish model.
It's also responsible for post-processing the embeddings.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
import json
import time
import numpy as np
import logging
import tensorflow.compat.v1 as tf # type: ignore
from src.embeddings.vgg import vggish_input
from src.embeddings.vgg import vggish_params
from src.embeddings.vgg import vggish_postprocess
from src.embeddings.vgg import vggish_slim

# Suppress TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.ERROR)
# Suppress deprecation warnings
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

# Set random seed for reproducibility
tf.set_random_seed(42)
np.random.seed(42)


CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
use_gpu     = config['settings']['use_gpu']
gpu_percent = config['settings']['gpu_percent']
debug       = config['settings']['debug']

CHECKPOINT_PATH = config['paths']['checkpoint_path']
PCA_PARAMS_PATH = config['paths']['pca_params_path']

if use_gpu:
    physical_devices = tf.config.experimental.list_physical_devices('GPU')

    if len(physical_devices) == 0:
        print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.RED}No GPU available. Switching to CPU...{Style.RESET_ALL}")
        use_gpu = False
    else:
        print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.GREEN}GPU available. Using GPU...{Style.RESET_ALL}")
        try:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
        except:
            print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.RED}Invalid device or cannot modify virtual devices once initialized.")
else:
    print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.YELLOW}GPU disabled. Switching to CPU...{Style.RESET_ALL}")



def extract_one_embedding(file: str) -> np.ndarray:
    """
    Extracts a single embedding from an audio file using a pre-trained VGGish model.
    
    Args:
        file (str): Path to the audio file.
    Returns:
        np.ndarray: A 128-dimensional embedding representing the audio file.
    Raises:
        ValueError: If the embedding dimension is not 128.
    Notes:
        - The audio file is loaded as mono and resampled to 16kHz.
        - The audio is split into 1-second segments, padded if necessary.
        - Embeddings are extracted for each segment and max-pooled across all segments.
    """
    # Generate VGGish input samples
    # - Resamples to 16kHz
    # - Converts audio to mono
    # - Frames a log-mel spectrogram into 0.96s examples with 50% overlap
    # The output is numpy array of shape [num_examples, num_frames, num_bands]
    # which is essentially always [num_examples, 96, 64]
    segments = vggish_input.wavfile_to_examples(file)
    segment_times = []

    # Ensure GPU use if available
    config = tf.ConfigProto()
    if use_gpu:
        config.gpu_options.allow_growth = True
        config.gpu_options.per_process_gpu_memory_fraction = gpu_percent
        print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.LIGHTCYAN_EX}GPU limited to {gpu_percent * 100} of total memory.{Style.RESET_ALL}")
    else:
        config.gpu_options.allow_growth = False
        config.gpu_options.visible_device_list = '' # Force CPU use
        if debug:
            print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.LIGHTCYAN_EX}GPU disabled. Using CPU...{Style.RESET_ALL}")

    overall_start = time.time()
    
    with tf.Graph().as_default(), tf.Session(config=config) as sess:
        # Define the VGGish model
        vggish_slim.define_vggish_slim(training=False)
        vggish_slim.load_vggish_slim_checkpoint(sess, CHECKPOINT_PATH)

        # Get input and output tensors
        features_tensor  = sess.graph.get_tensor_by_name(vggish_params.INPUT_TENSOR_NAME)
        embedding_tensor = sess.graph.get_tensor_by_name(vggish_params.OUTPUT_TENSOR_NAME)

        # Create a postprocessor
        pproc = vggish_postprocess.Postprocessor(PCA_PARAMS_PATH)

        # Run inference
        st = time.time()
        [embedding_batch] = sess.run([embedding_tensor], feed_dict={features_tensor: segments})
        segment_times.append(time.time() - st)

        if debug:
            print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.LIGHTMAGENTA_EX}Embedding shape: {embedding_batch.shape}{Style.RESET_ALL}")
        
        # Postprocess the embeddings
        postprocessed_batch = pproc.postprocess(embedding_batch)

        # Max pool the embeddings across all segments
        embedding = np.max(postprocessed_batch, axis=0)

    overall_end = time.time()
    if debug:
        print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.LIGHTMAGENTA_EX}Total embedding extraction time: {overall_end - overall_start:.2f} seconds{Style.RESET_ALL}")
        print(f"{Style.BRIGHT}[Embeddings]: {Style.DIM}{Fore.LIGHTMAGENTA_EX}Average segment embedding time: {np.mean(segment_times):.2f} seconds{Style.RESET_ALL}")

    return embedding

# def extract_audio_embeddings():
#     # Load the pre-trained VGGish model from TensorFlow Hub
#     vggish_model = hub.load('https://tfhub.dev/google/vggish/1')

#     # Load audio files
#     likes_folder = os.path.join(os.path.dirname(__file__), '..', 'data', 'Spotify Library', 'Likes')
#     audio_files  = os.listdir(likes_folder)
#     audio_files  = [f for f in audio_files if f.endswith('.mp3')]

#     # Sort audio_files by the numeric value before the first _
#     audio_files.sort(key=lambda x: int(x.split('_')[0]))

#     file_paths   = [os.path.join(os.path.dirname(__file__), '..', 'data', 'Spotify Library', 'Likes', file_name) for file_name in audio_files]

#     with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'Spotify Library', 'song_embeddings_max_pool.csv'), 'w') as f:
#         f.write("Song Name, Embedding\n")

#     ret_beds = []
#     for file in file_paths:
#         ind = file_paths.index(file)
#         print(f"{Fore.MAGENTA}Generating embeddings for file {audio_files[ind]}...                                             {Style.RESET_ALL}    ", end = '\r', flush=True)
#         # Load audio file
#         y, sr = librosa.load(file, sr=16000)  # Load as mono and resample to 16kHz

#         # STEP 1: Split the audio files into 1-second segments as VGGish requires
#         segments = []
#         num_segments = int(np.ceil(len(y) / sr))  # Calculate the number of 1-second segments
#         for i in range(num_segments):
#             start = i * sr
#             end = min((i + 1) * sr, len(y))
#             segment = y[start:end]
            
#             # Pad the segment if it is shorter than 1 second
#             if len(segment) < sr:
#                 segment = np.pad(segment, (0, sr - len(segment)), 'constant')
            
#             segments.append(segment)
        
#         print(f"{len(segments)} segments created...                                                           ", end = '\r', flush=True)
#         # STEP 2: Extract embeddings for each segment
#         embeddings = []
        
#         for i, segment in enumerate(segments):
#             # Convert the segment to the input format of VGGish
#             waveform = tf.convert_to_tensor(segment, dtype=tf.float32)

#             print(f"Generating embeddings for segment {i + 1}/{len(segments)}...                                             ", end = '\r', flush=True)
            
#             # Generate embedding using VGGish model
#             embedding = vggish_model(waveform)
            
#             # Ensure the embedding has the desired dimension
#             if embedding.shape[-1] != 128:
#                 raise ValueError('Embedding dimension is not 128: %s' % embedding.shape[-1])
            
#             embeddings.append(embedding.numpy())
        
#         song_embeddings = np.array(embeddings)
#         # Max pool the embeddings across all segments
#         song_embeddings = np.max(song_embeddings, axis=0)

#         # Save the embeddings to the next line of the CSV file
#         with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'Spotify Library', 'song_embeddings_max_pool.csv'), 'a') as f:
#             #current_csv = pd.read_csv(f)
#             print(f"Saving embeddings for file {audio_files[ind]}...                                             ", end = '\r', flush=True)
#             song = [subitem for item in song_embeddings.tolist() for subitem in item]
#             song_str = ", ".join([str(val) for val in song])
#             # Keep the contents of the CSV file the same, but add the new song embedding
#             f.write(f"{json.dumps(audio_files[ind])}, {json.dumps(song_str)}\n")

#         ret_beds.append(song_embeddings)

#         # if ind == 5:
#         #     break
#     return ret_beds

# def embed():
#     """
#     Extracts audio embeddings for songs in the 'Likes' folder, prints them, and saves them to a CSV file.

#     This function performs the following steps:
#     1. Extracts audio embeddings using the `extract_audio_embeddings` function.
#     2. Retrieves the list of audio files from the 'Likes' folder.
#     3. Sorts the audio files by the numeric value before the first underscore in their filenames.
#     4. Prints the embeddings for each song along with the corresponding filename.
#     5. Saves the embeddings to a CSV file named 'song_embeddings_full.csv' in the 'Spotify Library' folder.

#     The CSV file contains two columns:
#     - Song Name: The name of the audio file.
#     - Embedding: The audio embedding as a string.

#     Note:
#     - The function assumes that the audio files are in MP3 format and have filenames that start with a numeric value followed by an underscore.
#     - The function uses the `json.dumps` method to convert the song names and embeddings to JSON strings before writing them to the CSV file.
#     """
#     song_embeddings = extract_audio_embeddings()

#     likes_folder = os.path.join(os.path.dirname(__file__), '..', 'data', 'Spotify Library', 'Likes')
#     audio_files  = os.listdir(likes_folder)
#     audio_files  = [f for f in audio_files if f.endswith('.mp3')]
#     # Sort audio_files by the numeric value before the first _
#     audio_files.sort(key=lambda x: int(x.split('_')[0]))
#     print(f"\nSong embeddings is length: {len(song_embeddings)}")
#     for i, song in enumerate(song_embeddings):
#        print(f"Song {audio_files[i]}:\n {song}")
#        print("\n")

#     # Save the embeddings to a file mapping song name to embedding as a string
#     with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'Spotify Library', 'song_embeddings_full.csv'), 'w') as f:
#         f.write("Song Name, Embedding\n")
#         for i, song in enumerate(song_embeddings):
#             song = [subitem for item in song.tolist() for subitem in item]
#             song_str = ", ".join([str(val) for val in song])
#             f.write(f"{json.dumps(audio_files[i])}, {json.dumps(song_str)}\n")

#embed()
#extract_one_embedding(os.path.join(os.path.dirname(__file__), '..', 'data', 'spotify', 'to_embed.mp3'))