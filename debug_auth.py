import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.core.hashing import verify_password, hash_password

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text(
            "SELECT email, password_hash, role, is_active FROM users WHERE email = 'assureur@organisme.cm'"
        ))
        row = r.fetchone()
        if not row:
            print("UTILISATEUR INTROUVABLE")
            return
        print(f"email={row[0]} | role={row[2]} | actif={row[3]}")
        print(f"hash={row[1][:40]}...")

        for pwd in ["assureur123", "assureur", "password", "admin123"]:
            ok = verify_password(pwd, row[1])
            print(f"  '{pwd}' -> {'OK' if ok else 'FAUX'}")

asyncio.run(main())
