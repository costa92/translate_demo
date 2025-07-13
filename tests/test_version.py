"""Tests"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.translate_demo import __version__


def test_version():
    """Test version"""
    assert __version__ == '0.1.0'
