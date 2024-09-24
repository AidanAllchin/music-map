#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Retrieves tsv files and generates embeddings for them.
"""

import asyncio
import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style
from src.utils.ytdl_handler import download_best
from src.embeddings.vgg_maxpool import extract_one_embedding
import pandas as pd
from tqdm import tqdm

async def embed_row(row: pd.Series) -> list:
    """
    Embeds a row of the dataframe.

    This function takes a row of the dataframe as input, downloads the song, generates embeddings,
    and returns the embeddings.

    Args:
        row (pd.Series): A row of the dataframe.

    Returns:
        list: The embedding of the row [list of 128 floats].
    """
    # Download the song
    success, file_path = await download_best(
        search_query=row['Track Name'] + ' ' + row['Artists'], 
        target_length=row['Song Length (s)'],
        threshold=5,
        sp_id=row['Track ID']
    )

    if not success:
        print(f"{Style.BRIGHT}[EmbeddingsGenerator]: {Style.NORMAL}{Fore.RED}Error: Could not download {row['title']}.{Style.RESET_ALL}")
        return None

    # Generate the embeddings
    embedding = extract_one_embedding(file=file_path)

    return embedding

async def add_embeddings_to_tsv(tsv_path: str):
    """
    Adds embeddings to a TSV file.

    This function reads a TSV file, generates embeddings for each row, and adds these embeddings
    as a new column to the dataframe. The updated dataframe is then saved back to the TSV file.

    Args:
        tsv_path (str): The path to the TSV file.

    Raises:
        SystemExit: If the file does not exist or if the 'embeddings' column already exists in the dataframe.

    Notes:
        - The function checks if the file exists at the given path. If not, it prints an error message and exits.
        - It reads the TSV file into a pandas dataframe.
        - It ensures that the 'embeddings' column is not already present in the dataframe.
        - It iterates over each row of the dataframe, generating embeddings and appending them to a list.
        - The embeddings are added as a new column to the dataframe.
        - The updated dataframe is saved back to the TSV file.
        - A success message is printed upon completion.
    """
    # Check if the file exists
    if not os.path.exists(tsv_path):
        print(f"{Style.BRIGHT}[EmbeddingsGenerator]: {Style.NORMAL}{Fore.RED}Error: File not found.{Style.RESET_ALL}")
        sys.exit(1)

    # Read
    df = pd.read_csv(tsv_path, sep='\t')

    # Ensure 'embeddings' column is not already present
    if 'embeddings' in df.columns:
        print(f"{Style.BRIGHT}[EmbeddingsGenerator]: {Style.NORMAL}{Fore.RED}Error: 'embeddings' column already exists in the dataframe.{Style.RESET_ALL}")
        sys.exit(1)

    embeddings = []

    for _, row in tqdm(df.iterrows(), desc="Embedding rows", total=df.shape[0]):
        embeddings.append(await embed_row(row))

    # Add the embeddings to the dataframe
    df['embeddings'] = embeddings

    # Save the dataframe
    df.to_csv(tsv_path, sep='\t', index=False)

    print(f"{Style.BRIGHT}[EmbeddingsGenerator]: {Style.NORMAL}{Fore.GREEN}Embeddings added to {tsv_path}.{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(add_embeddings_to_tsv(sys.argv[1]))