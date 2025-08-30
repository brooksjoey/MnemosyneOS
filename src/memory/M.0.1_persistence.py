"""
M.0.1 — Persistence Utility Module
PURPOSE: Provide a simple, modular persistence layer for memory modules using SQLite (via SQLAlchemy).
INPUTS: table name, data dicts
ACTIONS:
  1. Initialize SQLite DB and tables if needed.
  2. Insert, query, and delete records.
OUTPUT/STATE: Persistent storage for memory events
ROLLBACK: Delete or revert records as needed
QUICKTEST: python -m memory.M.0.1_persistence --test
"""

import os
from typing import List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, Table, MetaData
from sqlalchemy.orm import sessionmaker

DB_PATH = os.environ.get("MNEMO_DB_PATH", "mnemo_memory.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
metadata = MetaData()
Session = sessionmaker(bind=engine, future=True)

# Example: L1 buffer table
def get_l1_table():
    return Table(
        "l1_buffer", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("timestamp", Float),
        Column("event_type", String),
        Column("content", String),
        Column("metadata", JSON),
    )

# L2 episodic table
def get_l2_table():
    return Table(
        "l2_episodes", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("l2_timestamp", Float),
        Column("event_type", String),
        Column("content", String),
        Column("metadata", JSON),
    )
    return Table(
        "l1_buffer", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("timestamp", Float),
        Column("event_type", String),
        Column("content", String),
        Column("metadata", JSON),
    )

def init_db():
    metadata.create_all(engine)

def insert_l1_event(event: Dict[str, Any]) -> int:
    table = get_l1_table()
    with engine.begin() as conn:
        result = conn.execute(table.insert().values(**event))
        return result.inserted_primary_key[0]

# L2 episodic persistence
def insert_l2_event(event: Dict[str, Any]) -> int:
    table = get_l2_table()
    with engine.begin() as conn:
        result = conn.execute(table.insert().values(**event))
        return result.inserted_primary_key[0]

def get_l1_events(limit: int = 10) -> List[Dict[str, Any]]:
    table = get_l2_table()
    with engine.begin() as conn:
        rows = conn.execute(table.select().order_by(table.c.l2_timestamp.desc()).limit(limit)).fetchall()
        return [dict(row._mapping) for row in rows]
    table = get_l1_table()
    with engine.begin() as conn:
    table = get_l2_table()
    with engine.begin() as conn:
        conn.execute(table.delete().where(table.c.id == event_id))
        rows = conn.execute(table.select().order_by(table.c.timestamp.desc()).limit(limit)).fetchall()
        return [dict(row._mapping) for row in rows]

def delete_l1_event(event_id: int):
    table = get_l1_table()
    with engine.begin() as conn:
        conn.execute(table.delete().where(table.c.id == event_id))

def quicktest():
    init_db()
    eid = insert_l1_event({"timestamp": 1.0, "event_type": "test", "content": "hello", "metadata": {}})
    events = get_l1_events(1)
    assert events and events[0]["id"] == eid
    delete_l1_event(eid)
    print("M.0.1 quicktest passed.")

if __name__ == "__main__":
    quicktest()
