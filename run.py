#!/usr/bin/env python3
"""
Upwork Discord Bot - Main Entry Point

Start with: python run.py

Everything is controlled from Discord using commands!
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f" .env file not found at {env_file}")
    exit(1)

# Check required token
if not os.getenv("DISCORD_BOT_TOKEN"):
    print(" DISCORD_BOT_TOKEN not set in .env")
    print("   Get your bot token from: https://discord.com/developers/applications")
    exit(1)

# Import after .env is loaded
from discord_bot import main

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" UPWORK DISCORD BOT - STARTING")
    print("=" * 70)
    print("\n✓ Configuration loaded")
    print("✓ Discord token found")
    print("✓ Connecting to Discord...\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBot stopped")
        exit(0)
    except Exception as e:
        print(f"\n Error: {e}")
        exit(1)
