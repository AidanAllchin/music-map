#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Retrieves tsv files and generates embeddings for them.
"""

import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from colorama import Fore, Style