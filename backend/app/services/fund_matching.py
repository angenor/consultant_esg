"""Service de scoring et recommandation de fonds verts.

Calcule un score de compatibilité (0-100) entre une entreprise et les fonds disponibles,
avec pondération configurable et détails explicatifs.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.entreprise import Entreprise
    from app.models.fonds_vert import FondsVert


# --- Pondération configurable via env ---

SCORING_WEIGHTS = {
    "pays_eligible": int(os.getenv("SCORING_WEIGHT_PAYS", "30")),
    "secteur_match": int(os.getenv("SCORING_WEIGHT_SECTEUR", "25")),
    "score_esg_ok": int(os.getenv("SCORING_WEIGHT_ESG", "30")),
    "montant_accessible": int(os.getenv("SCORING_WEIGHT_MONTANT", "15")),
}

# Bonus/malus supplémentaires
BONUS_DATE_LIMITE_PROCHE = 5   # date limite < 60 jours
BONUS_MODE_ACCES_DIRECT = 5    # mode_acces == "direct"
MALUS_ESG_TROP_BAS = -10       # score ESG < minimum - 20


# --- Mapping pays → ISO ---

PAYS_TO_ISO: dict[str, str] = {
    "côte d'ivoire": "CIV", "cote d'ivoire": "CIV", "ivory coast": "CIV",
    "sénégal": "SEN", "senegal": "SEN", "mali": "MLI",
    "burkina faso": "BFA", "togo": "TGO", "bénin": "BEN", "benin": "BEN",
    "niger": "NER", "guinée-bissau": "GNB", "cameroun": "CMR", "cameroon": "CMR",
    "ghana": "GHA", "kenya": "KEN", "tanzanie": "TZA", "éthiopie": "ETH",
    "nigeria": "NGA", "nigéria": "NGA",
    "guinée": "GIN", "guinee": "GIN",
    "congo": "COG", "rdc": "COD", "gabon": "GAB",
    "madagascar": "MDG", "mauritanie": "MRT",
    "tchad": "TCD", "centrafrique": "CAF",
    "rwanda": "RWA", "burundi": "BDI",
    "mozambique": "MOZ", "afrique du sud": "ZAF",
    "maroc": "MAR", "tunisie": "TUN", "algérie": "DZA", "algerie": "DZA",
    "égypte": "EGY", "egypte": "EGY",
}


def get_iso_code(pays: str | None) -> str | None:
    """Convertit un nom de pays en code ISO 3 lettres."""
    if not pays:
        return None
    pays_lower = pays.strip().lower()
    if len(pays_lower) == 3 and pays_lower.isalpha():
        return pays_lower.upper()
    return PAYS_TO_ISO.get(pays_lower)


# --- Résultat de scoring ---

@dataclass
class CompatibilityDetails:
    """Détails explicatifs du score de compatibilité."""
    pays_eligible: bool = False
    secteur_match: bool = False
    score_esg_ok: bool = False
    montant_accessible: bool = False
    bonus_date_limite: bool = False
    bonus_mode_direct: bool = False
    malus_esg_trop_bas: bool = False

    def to_dict(self) -> dict:
        return {
            "pays_eligible": self.pays_eligible,
            "secteur_match": self.secteur_match,
            "score_esg_ok": self.score_esg_ok,
            "montant_accessible": self.montant_accessible,
            "bonus_date_limite": self.bonus_date_limite,
            "bonus_mode_direct": self.bonus_mode_direct,
            "malus_esg_trop_bas": self.malus_esg_trop_bas,
        }


@dataclass
class FundScore:
    """Résultat du scoring d'un fonds pour une entreprise."""
    fonds: Any  # FondsVert at runtime
    compatibility_score: int
    details: CompatibilityDetails
    score_esg_minimum: float


def compute_compatibility(
    fonds: Any,
    entreprise: Any | None,
    entreprise_iso: str | None,
    best_esg_score: float | None,
) -> FundScore:
    """Calcule le score de compatibilité d'un fonds pour une entreprise."""
    compatibility = 0
    details = CompatibilityDetails()
    criteres = fonds.criteres_json or {}
    score_min = criteres.get("score_esg_minimum", 0)

    if not entreprise:
        return FundScore(
            fonds=fonds,
            compatibility_score=20,
            details=details,
            score_esg_minimum=score_min,
        )

    # Critère pays (+30)
    if fonds.pays_eligibles and entreprise_iso:
        if entreprise_iso in [p.upper() for p in fonds.pays_eligibles]:
            compatibility += SCORING_WEIGHTS["pays_eligible"]
            details.pays_eligible = True

    # Critère secteur (+25)
    if fonds.secteurs_json and entreprise.secteur:
        secteur_lower = entreprise.secteur.lower()
        sous_secteur_lower = (entreprise.sous_secteur or "").lower()
        if any(
            s.lower() in secteur_lower
            or secteur_lower in s.lower()
            or (sous_secteur_lower and s.lower() in sous_secteur_lower)
            for s in fonds.secteurs_json
        ):
            compatibility += SCORING_WEIGHTS["secteur_match"]
            details.secteur_match = True

    # Critère ESG (+30, +15 si >= 70%)
    if best_esg_score is not None:
        if best_esg_score >= score_min:
            compatibility += SCORING_WEIGHTS["score_esg_ok"]
            details.score_esg_ok = True
        elif best_esg_score >= score_min * 0.7:
            compatibility += SCORING_WEIGHTS["score_esg_ok"] // 2
            details.score_esg_ok = True  # partiel mais positif
        # Malus si trop loin du minimum
        if score_min > 0 and best_esg_score < score_min - 20:
            compatibility += MALUS_ESG_TROP_BAS
            details.malus_esg_trop_bas = True

    # Critère montant (+15)
    if fonds.montant_min and entreprise.chiffre_affaires:
        ca = float(entreprise.chiffre_affaires)
        if ca >= float(fonds.montant_min) * 0.5:
            compatibility += SCORING_WEIGHTS["montant_accessible"]
            details.montant_accessible = True

    # Bonus date limite proche (+5)
    if fonds.date_limite:
        days_remaining = (fonds.date_limite - date.today()).days
        if 0 < days_remaining <= 60:
            compatibility += BONUS_DATE_LIMITE_PROCHE
            details.bonus_date_limite = True

    # Bonus mode accès direct (+5)
    if fonds.mode_acces == "direct":
        compatibility += BONUS_MODE_ACCES_DIRECT
        details.bonus_mode_direct = True

    return FundScore(
        fonds=fonds,
        compatibility_score=max(0, min(compatibility, 100)),
        details=details,
        score_esg_minimum=score_min,
    )


def fund_score_to_dict(fs: FundScore) -> dict:
    """Convertit un FundScore en dict pour la réponse API."""
    f = fs.fonds
    criteres = f.criteres_json or {}
    acces_details = criteres.get("acces_details")

    return {
        "id": str(f.id),
        "nom": f.nom,
        "institution": f.institution,
        "type": f.type,
        "montant_min": float(f.montant_min) if f.montant_min else None,
        "montant_max": float(f.montant_max) if f.montant_max else None,
        "devise": f.devise,
        "secteurs_json": f.secteurs_json,
        "pays_eligibles": f.pays_eligibles,
        "criteres_json": criteres,
        "date_limite": f.date_limite.isoformat() if f.date_limite else None,
        "url_source": f.url_source,
        "mode_acces": f.mode_acces,
        "is_active": f.is_active,
        "compatibility_score": fs.compatibility_score,
        "compatibility_details": fs.details.to_dict(),
        "score_esg_minimum": fs.score_esg_minimum,
        "acces_details": acces_details,
    }


# --- Cache mémoire simple avec TTL ---

@dataclass
class _CacheEntry:
    data: list[dict]
    timestamp: float
    filters_key: str


_cache: dict[str, _CacheEntry] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _make_cache_key(
    entreprise_id: str,
    type_filter: str | None,
    montant_max: float | None,
    secteur: str | None,
) -> str:
    return f"{entreprise_id}:{type_filter or ''}:{montant_max or ''}:{secteur or ''}"


def invalidate_cache(entreprise_id: str | None = None) -> None:
    """Invalide le cache — appelé quand le profil ou les fonds changent."""
    if entreprise_id:
        keys_to_remove = [k for k in _cache if k.startswith(str(entreprise_id))]
        for k in keys_to_remove:
            del _cache[k]
    else:
        _cache.clear()


async def get_recommendations(
    db: AsyncSession,
    entreprise: Any | None,
    *,
    type_filter: str | None = None,
    montant_max: float | None = None,
    secteur_filter: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Retourne les fonds recommandés triés par compatibilité.

    Args:
        db: Session de base de données
        entreprise: Entreprise de l'utilisateur (ou None)
        type_filter: Filtrer par type (pret, subvention, garantie)
        montant_max: Montant maximum souhaité
        secteur_filter: Filtrer par secteur
        limit: Nombre max de résultats
    """
    from sqlalchemy import select

    from app.models.esg_score import ESGScore
    from app.models.fonds_vert import FondsVert

    ent_id = str(entreprise.id) if entreprise else "anonymous"
    cache_key = _make_cache_key(ent_id, type_filter, montant_max, secteur_filter)

    # Vérifier le cache
    cached = _cache.get(cache_key)
    if cached and (time.time() - cached.timestamp) < _CACHE_TTL_SECONDS:
        return cached.data[:limit]

    # Meilleur score ESG
    best_esg_score: float | None = None
    if entreprise:
        score_result = await db.execute(
            select(ESGScore)
            .where(ESGScore.entreprise_id == entreprise.id)
            .order_by(ESGScore.score_global.desc().nulls_last())
            .limit(1)
        )
        best_score_obj = score_result.scalar_one_or_none()
        if best_score_obj and best_score_obj.score_global:
            best_esg_score = float(best_score_obj.score_global)

    # Requête fonds actifs avec filtres
    query = select(FondsVert).where(FondsVert.is_active == True)  # noqa: E712
    if type_filter:
        query = query.where(FondsVert.type == type_filter)
    result = await db.execute(query)
    fonds_list = result.scalars().all()

    entreprise_iso = get_iso_code(entreprise.pays) if entreprise else None

    # Scoring
    scores: list[FundScore] = []
    for f in fonds_list:
        fs = compute_compatibility(f, entreprise, entreprise_iso, best_esg_score)

        # Filtre montant max
        if montant_max and f.montant_min:
            if float(f.montant_min) > montant_max:
                continue

        # Filtre secteur
        if secteur_filter and f.secteurs_json:
            secteur_lower = secteur_filter.lower()
            if not any(
                s.lower() in secteur_lower or secteur_lower in s.lower()
                for s in f.secteurs_json
            ):
                continue

        scores.append(fs)

    # Tri par score décroissant
    scores.sort(key=lambda s: s.compatibility_score, reverse=True)

    recommendations = [fund_score_to_dict(s) for s in scores]

    # Mettre en cache
    _cache[cache_key] = _CacheEntry(
        data=recommendations,
        timestamp=time.time(),
        filters_key=cache_key,
    )

    return recommendations[:limit]
