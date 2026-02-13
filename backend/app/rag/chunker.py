"""
Découpage intelligent de texte en chunks pour le RAG.
Respecte les limites de paragraphes et de phrases autant que possible.
"""

import re


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 200,
) -> list[dict]:
    """
    Découpe un texte en chunks de ~chunk_size caractères avec overlap.
    Essaie de couper aux limites de paragraphes, puis de phrases.

    Retourne une liste de dicts : {"text": str, "index": int, "page": int | None}
    """
    if not text or not text.strip():
        return []

    # Détecter les marqueurs de page [Page N]
    page_markers = _find_page_markers(text)

    # Découper en paragraphes
    paragraphs = _split_paragraphs(text)

    chunks = []
    current_chunk = ""
    current_start = 0  # position dans le texte original

    for para in paragraphs:
        # Si le paragraphe seul dépasse chunk_size, le découper en phrases
        if len(para) > chunk_size:
            # Flush le chunk en cours
            if current_chunk.strip():
                chunks.append(_make_chunk(current_chunk.strip(), len(chunks), current_start, page_markers))
            current_chunk = ""

            # Découper le gros paragraphe en phrases
            sentences = _split_sentences(para)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > chunk_size and current_chunk.strip():
                    chunks.append(_make_chunk(current_chunk.strip(), len(chunks), current_start, page_markers))
                    # Overlap : reprendre la fin du chunk précédent
                    current_start += len(current_chunk) - overlap
                    current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk += sentence
            continue

        # Vérifier si ajouter ce paragraphe dépasse la taille
        candidate = current_chunk + ("\n\n" if current_chunk else "") + para
        if len(candidate) > chunk_size and current_chunk.strip():
            chunks.append(_make_chunk(current_chunk.strip(), len(chunks), current_start, page_markers))
            # Overlap
            current_start += len(current_chunk) - overlap
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + para
        else:
            current_chunk = candidate

    # Dernier chunk
    if current_chunk.strip():
        chunks.append(_make_chunk(current_chunk.strip(), len(chunks), current_start, page_markers))

    return chunks


def _make_chunk(text: str, index: int, start_pos: int, page_markers: list[tuple[int, int]]) -> dict:
    """Crée un dict chunk avec détection de numéro de page."""
    page = None
    for marker_pos, page_num in reversed(page_markers):
        if marker_pos <= start_pos:
            page = page_num
            break
    return {"text": text, "index": index, "page": page}


def _find_page_markers(text: str) -> list[tuple[int, int]]:
    """Trouve les marqueurs [Page N] dans le texte et retourne [(position, numéro)]."""
    markers = []
    for match in re.finditer(r"\[Page\s+(\d+)\]", text):
        markers.append((match.start(), int(match.group(1))))
    return markers


def _split_paragraphs(text: str) -> list[str]:
    """Découpe le texte en paragraphes (séparés par des lignes vides)."""
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_sentences(text: str) -> list[str]:
    """Découpe un texte en phrases en préservant la ponctuation."""
    # Séparer aux points, points d'interrogation, points d'exclamation
    # suivis d'un espace ou fin de texte
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s + " " for s in sentences if s.strip()]
