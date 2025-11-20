# backend/database.py
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, select
from sqlalchemy.sql import insert
from dataclasses import dataclass

DB_URL = os.getenv('AIML_NEXUS_DB', 'sqlite:///./aiml_nexus.db')

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = MetaData()

conversations = Table(
    'conversations',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', String(128)),
    Column('user_message', Text),
    Column('reply', Text),
)

metadata.create_all(engine)

def save_turn(user_id: str, user_message: str, reply: str):
    with engine.connect() as conn:
        stmt = insert(conversations).values(user_id=user_id, user_message=user_message, reply=reply)
        conn.execute(stmt)

@dataclass
class Turn:
    id: int
    user_id: str
    user_message: str
    reply: str

def get_last_n_turns(n: int = 20):
    with engine.connect() as conn:
        stmt = select(conversations).order_by(conversations.c.id.desc()).limit(n)
        res = conn.execute(stmt).fetchall()
        # map to dataclass and reverse so oldest-first
        turns = [Turn(id=r.id, user_id=r.user_id, user_message=r.user_message, reply=r.reply) for r in res]
        return list(reversed(turns))