"""python seed.py — creates default users if they don't exist."""

import asyncio

from sqlalchemy import select

from app.database import engine, async_session
from app.models.base import Base
from app.modules.auth import User, hash_password

USERS = [
    {"name": "Rafael", "email": "admin@assistant.dev", "password": "admin123", "role": "admin"},
    {"name": "Frontend Team", "email": "user@assistant.dev", "password": "user123", "role": "user"},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        for u in USERS:
            exists = await session.execute(select(User).where(User.email == u["email"]))
            if exists.scalar_one_or_none():
                print(f"  skip  {u['email']} (exists)")
                continue
            session.add(User(
                name=u["name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
            ))
            print(f"  added {u['email']}  pw={u['password']}  role={u['role']}")
        await session.commit()
    print("done.")


if __name__ == "__main__":
    asyncio.run(seed())
