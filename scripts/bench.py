scripts/bench.py
import asyncio, httpx, time, statistics, random

API_BASE = "http://localhost:8000"
API_KEY = "dev-key-123"

async def hit(session, q):
    t0 = time.perf_counter()
    r = await session.get(f"{API_BASE}/recall", params={"query": q, "k": 5}, headers={"Authorization": f"Bearer {API_KEY}"})
    r.raise_for_status()
    return (time.perf_counter() - t0) * 1000.0

async def run_bench(rps=100, duration_s=10):
    lat = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        start = time.perf_counter()
        while time.perf_counter() - start < duration_s:
            tasks = []
            for _ in range(rps):
                q = random.choice(["project status", "meeting notes", "travel plan", "architecture", "database index"])
                tasks.append(asyncio.create_task(hit(client, q)))
            lat += await asyncio.gather(*tasks)
        p95 = statistics.quantiles(lat, n=100)[94]
        print(f"count={len(lat)} p95={p95:.2f}ms mean={statistics.mean(lat):.2f}ms")
    return lat

if __name__ == "__main__":
    asyncio.run(run_bench())