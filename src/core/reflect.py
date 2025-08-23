src/core/reflect.py
from .consistency import reflect_beliefs
from ..utils.metrics import reflect_counter

async def run_reflection(db):
    await reflect_beliefs(db)
    reflect_counter.inc()