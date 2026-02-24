#!/usr/bin/env python3
"""Generate OAUTH_SECRET_KEY for .env. Run: python scripts/generate_oauth_key.py"""
import secrets

if __name__ == "__main__":
    key = secrets.token_urlsafe(32)
    print(f"Add to .env:\nOAUTH_SECRET_KEY={key}")
