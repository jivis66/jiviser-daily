#!/usr/bin/env python3
"""
Daily Agent CLI
Usage: python daily.py [options]
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.daily import main

if __name__ == "__main__":
    main()
