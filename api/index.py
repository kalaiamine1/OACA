"""
Vercel serverless function entry point for Flask app
"""
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from configuration import ensure_default_user

# Ensure default user exists on cold start
# Note: This runs on each cold start, but MongoDB operations are idempotent
try:
    ensure_default_user()
except Exception as e:
    # Log but don't fail - MongoDB connection might not be available yet
    print(f"Warning: Could not ensure default user: {e}")

# Export the Flask app for Vercel
# Vercel's @vercel/python automatically detects Flask apps

