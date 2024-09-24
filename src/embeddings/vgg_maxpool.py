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
print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.LIGHTCYAN_EX}Loading TensorFlow. This may take a while...{Style.RESET_ALL}")
import json
import time
import numpy as np
import logging
import warnings
import tensorflow.compat.v1 as tf # type: ignore
print(f"{Style.BRIGHT}[Embeddings]: {Style.NORMAL}{Fore.CYAN}TensorFlow version: {tf.__version__} loaded.{Style.RESET_ALL}")
from src.embeddings.vgg import vggish_input
from src.embeddings.vgg import vggish_params
from src.embeddings.vgg import vggish_postprocess
from src.embeddings.vgg import vggish_slim

# Suppress TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.ERROR)
# Suppress deprecation warnings
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
warnings.filterwarnings("ignore")
tf.compat.v1.disable_eager_execution()
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

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

    config.log_device_placement = False
    config.allow_soft_placement = True

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