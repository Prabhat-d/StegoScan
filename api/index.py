import sys
import os

# Add project root directory to sys.path so Vercel finds app.py and blueprinted modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
