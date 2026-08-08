import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import asyncsessionlocal
from models import Providers, Models

async def seed_data():
    async with asyncsessionlocal() as db:
        # 1. Add Providers
        mock = Providers(provider_id=3,name="Mock",description="mock testing ofcourse")
        db.add_all([mock])
        await db.commit()

        # 2. Add Models

        m3 = Models(
            model_id=3,
            model_name = 'mock-llm',
            global_rpm=100000,
            global_rpd = 10000000,
            global_tpm = 10000000,
            global_tpd = 1000000000,
            provider_id = 3
        )
        m4 = Models(
                    model_id=4,
                    model_name = 'mock-llm-fallback',
                    global_rpm=100000,
                    global_rpd = 10000000,
                    global_tpm = 10000000,
                    global_tpd = 1000000000,
                    provider_id = 3
                )

        db.add_all([m3,m4])
        await db.commit()

    print("Successfully seeded exact Providers and Models!")

if __name__ == "__main__":
    asyncio.run(seed_data())