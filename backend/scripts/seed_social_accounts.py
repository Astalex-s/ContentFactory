"""Seed script to create test social accounts."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.social_account import SocialAccount, SocialPlatform
from app.core.config import get_settings

DEFAULT_USER_ID = get_settings().DEFAULT_USER_ID


async def seed_social_accounts():
    """Create test social account for YouTube."""
    async with async_session_maker() as session:
        # Check if accounts already exist
        result = await session.execute(
            select(SocialAccount).where(SocialAccount.user_id == DEFAULT_USER_ID)
        )
        existing = result.scalars().all()

        if existing:
            print(f"Found {len(existing)} existing social accounts:")
            for acc in existing:
                print(f"  - {acc.platform}: {acc.channel_title or acc.channel_id or 'N/A'}")
            return

        # Create YouTube account
        youtube_account = SocialAccount(
            user_id=DEFAULT_USER_ID,
            platform=SocialPlatform.YOUTUBE,
            channel_id="UCIBg8LmumCb39bHTbo7vWDQ",
            channel_title="Test YouTube Channel",
            access_token="test_youtube_token",
            refresh_token="test_youtube_refresh",
        )
        session.add(youtube_account)

        await session.commit()
        print("✅ Created test social account:")
        print("  - YouTube: Test YouTube Channel")


if __name__ == "__main__":
    asyncio.run(seed_social_accounts())
