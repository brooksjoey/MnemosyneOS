scripts/load_seed.py
import asyncio, httpx, random
from faker import Faker

fake = Faker()

API_BASE = "http://localhost:8000"
API_KEY = "dev-key-123"

async def seed(n=100_000):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient(timeout=10) as client:
        for i in range(n):
            content = f"{fake.sentence()} {fake.paragraph()} {fake.company()} {fake.name()}"
            md = {"tag": random.choice(["work","personal","research"])}
            r = await client.post(f"{API_BASE}/remember", headers=headers, json={"source_id": f"seed:{i%1000}", "content": content, "metadata": md})
            if i % 1000 == 0:
                print("seeded", i)
    print("done")

if __name__ == "__main__":
    asyncio.run(seed())