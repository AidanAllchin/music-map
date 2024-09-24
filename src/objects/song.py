#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Created on Tue Sep 24 2024

This script contains the Song class, which represents a song object.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
import numpy as np
import pandas as pd
from typing import Tuple


"""
id: int
spotify_id: str
name: str
artists: list[str]
album: str
duration: float
spotify_url: str
youtube_url: str
waveform: np.ndarray
embedding: np.ndarray
"""
class Song:
    def __init__(self, db_id: int, spotify_id: str, name: str, artists: list[str], album: str, duration: float, spotify_url: str, youtube_url: str | None, waveform: np.ndarray | None, embedding: np.ndarray | None):
        """
        Initializes a new instance of the Song class.

        Args:
        - db_id: int
            The unique identifier of the song in the database.
        - spotify_id: str
            The Spotify ID of the song.
        - name: str
            The name of the song.
        - artists: list[str]
            The artists of the song.
        - album: str
            The album of the song.
        - duration: float
            The duration of the song.
        - spotify_url: str
            The Spotify URL of the song.
        - youtube_url: str
            The YouTube URL of the song.
        - waveform: np.ndarray
            The waveform of the song.
        - embedding: np.ndarray
            The embedding of the song.
        """
        self.db_id = db_id
        self.spotify_id = spotify_id
        self.name = name
        self.artists = artists
        self.album = album
        self.duration = duration
        self.spotify_url = spotify_url
        self.youtube_url = youtube_url
        self.waveform = waveform
        self.embedding = embedding

    def __str__(self) -> str:
        """
        Returns a string representation of the Song object.

        Returns:
        - str
            A string representation of the Song object.
        """
        return f"Song: {self.name} - {', '.join(self.artists)}"

    def update_embedding(self, embedding: np.ndarray):
        """
        Updates the embedding of the song.

        Args:
        - embedding: np.ndarray
            The new embedding of the song.
        """
        self.embedding = embedding
    
    def update_waveform(self, waveform: np.ndarray):
        """
        Updates the waveform of the song.

        Args:
        - waveform: np.ndarray
            The new waveform of the song.
        """
        self.waveform = waveform

    @classmethod
    def to_dict(self) -> dict:
        """
        Converts the Song object to a dictionary.

        Returns:
        - dict
            A dictionary representation of the Song object.
        """
        return {
            'db_id': self.db_id,
            'spotify_id': self.spotify_id,
            'name': self.name,
            'artists': self.artists,
            'album': self.album,
            'duration': self.duration,
            'spotify_url': self.spotify_url,
            'youtube_url': self.youtube_url,
            'waveform': self.waveform,
            'embedding': self.embedding
        }
    
    @classmethod
    def to_pd_series(self) -> pd.Series:
        """
        Converts the Song object to a Pandas Series.

        Returns:
        - pd.Series
            A Pandas Series representation of the Song object.
        """
        return pd.Series(self.to_dict())