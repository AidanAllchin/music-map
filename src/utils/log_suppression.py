#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Suppresses the logger output.
"""
import os, sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

class SuppressLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

    def info(self, msg):
        pass