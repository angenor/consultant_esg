"""
Seed principal — exécutable avec : python -m app.seed

Exécute tous les seeds dans l'ordre :
  1. Skills builtin
  2. Référentiels ESG
  3. Fonds verts
  4. Benchmarks sectoriels
  5. Fonds chunks (RAG) — nécessite VOYAGE_API_KEY
  6. Report templates
  7. Données de démo (admin + entreprise + scores)
"""

import asyncio
import sys

from app.core.database import async_session
from app.seed.seed_skills import seed_skills
from app.seed.seed_referentiels import seed_referentiels
from app.seed.seed_fonds import seed_fonds
from app.seed.seed_benchmarks import seed_benchmarks
from app.seed.seed_fonds_chunks import seed_fonds_chunks
from app.seed.seed_report_templates import seed_report_templates
from app.seed.seed_demo import seed_demo


async def main():
    async with async_session() as db:
        print("=== Seed ESG Advisor ===\n")

        n = await seed_skills(db)
        print(f"[1/7] Skills builtin : {n} insérés")

        n = await seed_referentiels(db)
        print(f"[2/7] Référentiels ESG : {n} insérés/mis à jour")

        n = await seed_fonds(db)
        print(f"[3/7] Fonds verts : {n} insérés")

        n = await seed_benchmarks(db)
        print(f"[4/7] Benchmarks sectoriels : {n} insérés")

        try:
            n = await seed_fonds_chunks(db)
            print(f"[5/7] Fonds chunks (RAG) : {n} insérés")
        except Exception as e:
            print(f"[5/7] Fonds chunks (RAG) : skip ({e})")

        n = await seed_report_templates(db)
        print(f"[6/7] Report templates : {n} insérés")

        n = await seed_demo(db)
        print(f"[7/7] Données de démo : {n} objets créés")

        print("\n=== Seed terminé ===")


if __name__ == "__main__":
    asyncio.run(main())
