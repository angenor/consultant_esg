"""Tests unitaires pour le service de scoring fund_matching."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.fund_matching import (
    SCORING_WEIGHTS,
    CompatibilityDetails,
    compute_compatibility,
    get_iso_code,
    invalidate_cache,
    _cache,
)


# --- Helpers pour créer des mocks ---


def _make_fonds(**kwargs):
    """Crée un mock FondsVert avec des valeurs par défaut."""
    defaults = {
        "id": "fonds-1",
        "nom": "Fonds Test",
        "institution": "Institution Test",
        "type": "subvention",
        "montant_min": 1_000_000,
        "montant_max": 10_000_000,
        "devise": "USD",
        "secteurs_json": ["agriculture", "énergie"],
        "pays_eligibles": ["CIV", "SEN", "MLI"],
        "criteres_json": {"score_esg_minimum": 50},
        "date_limite": None,
        "url_source": "https://example.com",
        "mode_acces": "banque_partenaire",
        "is_active": True,
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_entreprise(**kwargs):
    """Crée un mock Entreprise avec des valeurs par défaut."""
    defaults = {
        "id": "ent-1",
        "nom": "AgriTech CI",
        "secteur": "Agriculture",
        "sous_secteur": "cultures vivrières",
        "pays": "Côte d'Ivoire",
        "chiffre_affaires": 5_000_000,
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


# --- Tests get_iso_code ---


class TestGetIsoCode:
    def test_nom_pays_connu(self):
        assert get_iso_code("Côte d'Ivoire") == "CIV"

    def test_nom_pays_sans_accent(self):
        assert get_iso_code("cote d'ivoire") == "CIV"

    def test_code_iso_existant(self):
        assert get_iso_code("CIV") == "CIV"

    def test_code_iso_minuscule(self):
        assert get_iso_code("sen") == "SEN"

    def test_pays_none(self):
        assert get_iso_code(None) is None

    def test_pays_inconnu(self):
        assert get_iso_code("Atlantide") is None

    def test_pays_avec_espaces(self):
        assert get_iso_code("  Sénégal  ") == "SEN"


# --- Tests compute_compatibility ---


class TestComputeCompatibility:
    """Tests de la fonction de scoring principal."""

    def test_entreprise_civ_agriculture_score_complet(self):
        """Entreprise CIV + agriculture + score ESG OK + CA OK → score max."""
        fonds = _make_fonds()
        entreprise = _make_entreprise()

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.compatibility_score == 100
        assert result.details.pays_eligible is True
        assert result.details.secteur_match is True
        assert result.details.score_esg_ok is True
        assert result.details.montant_accessible is True

    def test_entreprise_none_retourne_20(self):
        """Sans entreprise, score par défaut = 20."""
        fonds = _make_fonds()
        result = compute_compatibility(fonds, None, None, None)
        assert result.compatibility_score == 20

    def test_pays_non_eligible(self):
        """Entreprise d'un pays non éligible → pas de bonus pays."""
        fonds = _make_fonds(pays_eligibles=["SEN", "MLI"])
        entreprise = _make_entreprise()

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.details.pays_eligible is False
        # Devrait avoir secteur + ESG + montant mais pas pays
        expected = (
            SCORING_WEIGHTS["secteur_match"]
            + SCORING_WEIGHTS["score_esg_ok"]
            + SCORING_WEIGHTS["montant_accessible"]
        )
        assert result.compatibility_score == expected

    def test_secteur_non_correspondant(self):
        """Secteur qui ne matche pas → pas de bonus secteur."""
        fonds = _make_fonds(secteurs_json=["industrie", "mines"])
        entreprise = _make_entreprise(secteur="Finance")

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.details.secteur_match is False

    def test_sous_secteur_match(self):
        """Le sous-secteur est aussi pris en compte pour le matching."""
        fonds = _make_fonds(secteurs_json=["cultures vivrières"])
        entreprise = _make_entreprise(secteur="Autre", sous_secteur="cultures vivrières")

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.details.secteur_match is True

    def test_score_esg_insuffisant_partiel(self):
        """Score ESG >= 70% du minimum → bonus partiel."""
        fonds = _make_fonds(criteres_json={"score_esg_minimum": 60})
        entreprise = _make_entreprise()

        # 42 >= 60 * 0.7 (42) → partiel
        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=42)

        assert result.details.score_esg_ok is True
        # Score partiel = score_esg_ok // 2
        assert result.compatibility_score < 100

    def test_score_esg_none(self):
        """Sans score ESG → pas de bonus ESG."""
        fonds = _make_fonds()
        entreprise = _make_entreprise()

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=None)

        assert result.details.score_esg_ok is False

    def test_malus_esg_trop_bas(self):
        """Score ESG bien en dessous du minimum → malus appliqué."""
        fonds = _make_fonds(criteres_json={"score_esg_minimum": 80})
        entreprise = _make_entreprise()

        # 50 < 80 - 20 (60) → malus
        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=50)

        assert result.details.malus_esg_trop_bas is True

    def test_montant_non_accessible(self):
        """CA trop faible par rapport au montant minimum → pas de bonus."""
        fonds = _make_fonds(montant_min=100_000_000)
        entreprise = _make_entreprise(chiffre_affaires=1_000_000)

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.details.montant_accessible is False

    def test_bonus_date_limite_proche(self):
        """Date limite dans les 60 jours → bonus."""
        fonds = _make_fonds(date_limite=date.today() + timedelta(days=30))
        entreprise = _make_entreprise()

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.details.bonus_date_limite is True

    def test_pas_bonus_date_limite_lointaine(self):
        """Date limite dans plus de 60 jours → pas de bonus."""
        fonds = _make_fonds(date_limite=date.today() + timedelta(days=120))
        entreprise = _make_entreprise()

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.details.bonus_date_limite is False

    def test_bonus_mode_acces_direct(self):
        """Mode accès direct → bonus."""
        fonds = _make_fonds(mode_acces="direct")
        entreprise = _make_entreprise()

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.details.bonus_mode_direct is True

    def test_score_jamais_negatif(self):
        """Le score ne descend jamais en dessous de 0."""
        fonds = _make_fonds(
            pays_eligibles=["USA"],
            secteurs_json=["espace"],
            criteres_json={"score_esg_minimum": 95},
            montant_min=999_999_999_999,
        )
        entreprise = _make_entreprise(chiffre_affaires=100, secteur="Boulangerie")

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=10)

        assert result.compatibility_score >= 0

    def test_score_plafonne_a_100(self):
        """Le score ne dépasse jamais 100."""
        fonds = _make_fonds(
            mode_acces="direct",
            date_limite=date.today() + timedelta(days=10),
        )
        entreprise = _make_entreprise()

        result = compute_compatibility(fonds, entreprise, "CIV", best_esg_score=70)

        assert result.compatibility_score <= 100


# --- Tests du profil type : entreprise CIV + agriculture → fonds UEMOA en premier ---


class TestProfilEntreprise:
    """Vérifie la cohérence des résultats pour des profils types."""

    def test_civ_agriculture_prefere_uemoa(self):
        """Entreprise CIV + agriculture doit scorer plus haut sur fonds UEMOA."""
        fonds_uemoa = _make_fonds(
            nom="BOAD",
            pays_eligibles=["CIV", "SEN", "MLI", "BFA", "TGO", "BEN", "NER", "GNB"],
            secteurs_json=["agriculture", "énergie", "infrastructure"],
        )
        fonds_global = _make_fonds(
            nom="GCF",
            pays_eligibles=["USA", "GBR", "DEU", "FRA"],
            secteurs_json=["tous secteurs"],
        )
        entreprise = _make_entreprise()

        score_uemoa = compute_compatibility(fonds_uemoa, entreprise, "CIV", 70)
        score_global = compute_compatibility(fonds_global, entreprise, "CIV", 70)

        assert score_uemoa.compatibility_score > score_global.compatibility_score

    def test_sans_score_esg_recommande_fonds_sans_minimum(self):
        """Entreprise sans score ESG → mieux matchée avec fonds sans minimum ESG."""
        fonds_strict = _make_fonds(
            nom="Fonds strict",
            criteres_json={"score_esg_minimum": 70},
        )
        fonds_souple = _make_fonds(
            nom="Fonds souple",
            criteres_json={"score_esg_minimum": 0},
        )
        entreprise = _make_entreprise()

        score_strict = compute_compatibility(fonds_strict, entreprise, "CIV", None)
        score_souple = compute_compatibility(fonds_souple, entreprise, "CIV", None)

        # Les deux n'ont pas de bonus ESG, donc score identique (pas de malus non plus)
        assert score_strict.compatibility_score == score_souple.compatibility_score

    def test_hors_uemoa_prefere_fonds_internationaux(self):
        """Entreprise hors zone UEMOA → fonds internationaux mieux scorés."""
        fonds_uemoa = _make_fonds(
            nom="FAGACE",
            pays_eligibles=["CIV", "SEN", "MLI"],
        )
        fonds_international = _make_fonds(
            nom="BAD",
            pays_eligibles=["KEN", "TZA", "GHA", "NGA"],
        )
        entreprise = _make_entreprise(pays="Kenya")

        score_uemoa = compute_compatibility(fonds_uemoa, entreprise, "KEN", 70)
        score_intl = compute_compatibility(fonds_international, entreprise, "KEN", 70)

        assert score_intl.compatibility_score > score_uemoa.compatibility_score


# --- Tests compatibility_details (explicabilité) ---


class TestCompatibilityDetails:
    def test_to_dict_complet(self):
        details = CompatibilityDetails(
            pays_eligible=True,
            secteur_match=True,
            score_esg_ok=False,
            montant_accessible=True,
        )
        d = details.to_dict()
        assert d["pays_eligible"] is True
        assert d["secteur_match"] is True
        assert d["score_esg_ok"] is False
        assert d["montant_accessible"] is True
        assert d["bonus_date_limite"] is False
        assert d["bonus_mode_direct"] is False
        assert d["malus_esg_trop_bas"] is False


# --- Tests cache ---


class TestCache:
    def test_invalidate_cache_specific(self):
        """invalidate_cache(entreprise_id) supprime les entrées correspondantes."""
        _cache["ent-1:pret::"] = MagicMock()
        _cache["ent-1:::"] = MagicMock()
        _cache["ent-2:::"] = MagicMock()

        invalidate_cache("ent-1")

        assert "ent-1:pret::" not in _cache
        assert "ent-1:::" not in _cache
        assert "ent-2:::" in _cache

        # Cleanup
        _cache.clear()

    def test_invalidate_cache_all(self):
        """invalidate_cache() sans argument vide tout le cache."""
        _cache["key1"] = MagicMock()
        _cache["key2"] = MagicMock()

        invalidate_cache()

        assert len(_cache) == 0
