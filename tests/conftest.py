import sys
from pathlib import Path

# Add project root to sys.path to allow importing modules from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
