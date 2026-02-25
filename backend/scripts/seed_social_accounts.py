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
    """Create test social accounts for YouTube and VK."""
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
            
            # Update VK account if it exists but has no channel info
            vk_account = next((acc for acc in existing if acc.platform == SocialPlatform.VK), None)
            if vk_account and not vk_account.channel_id:
                print("Updating VK account with channel info...")
                vk_account.channel_id = "-12345678"
                vk_account.channel_title = "Тестовая группа VK"
                await session.commit()
                print("✅ VK account updated")
            return

        # Create YouTube account
        youtube_account = SocialAccount(
            user_id=DEFAULT_USER_ID,
            platform=SocialPlatform.YOUTUBE,
            channel_id="UCIBg8LmumCb39bHTbo7vWDQ",
            channel_title="Алексей Остафьев",
            access_token="test_youtube_token",
            refresh_token="test_youtube_refresh",
        )
        session.add(youtube_account)

        # Create VK account
        vk_account = SocialAccount(
            user_id=DEFAULT_USER_ID,
            platform=SocialPlatform.VK,
            channel_id="-12345678",
            channel_title="Тестовая группа VK",
            access_token="test_vk_token",
            refresh_token=None,
        )
        session.add(vk_account)

        await session.commit()
        print("✅ Created 2 test social accounts:")
        print("  - YouTube: Алексей Остафьев")
        print("  - VK: Тестовая группа VK")


if __name__ == "__main__":
    asyncio.run(seed_social_accounts())
