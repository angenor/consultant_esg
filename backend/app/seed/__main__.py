"""
Seed principal — exécutable avec : python -m app.seed

Exécute tous les seeds dans l'ordre :
  1. Skills builtin
  2. Référentiels ESG
  3. Fonds verts
  4. Benchmarks sectoriels
"""

import asyncio
import sys

from app.core.database import async_session
from app.seed.seed_skills import seed_skills
from app.seed.seed_referentiels import seed_referentiels
from app.seed.seed_fonds import seed_fonds
from app.seed.seed_benchmarks import seed_benchmarks


async def main():
    async with async_session() as db:
        print("=== Seed ESG Advisor ===\n")

        n = await seed_skills(db)
        print(f"[1/4] Skills builtin : {n} insérés")

        n = await seed_referentiels(db)
        print(f"[2/4] Référentiels ESG : {n} insérés")

        n = await seed_fonds(db)
        print(f"[3/4] Fonds verts : {n} insérés")

        n = await seed_benchmarks(db)
        print(f"[4/4] Benchmarks sectoriels : {n} insérés")

        print("\n=== Seed terminé ===")


if __name__ == "__main__":
    asyncio.run(main())
