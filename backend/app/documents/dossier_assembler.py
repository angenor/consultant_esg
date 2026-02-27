"""
Assembleur de dossiers de candidature en archive ZIP.
Regroupe tous les documents générés dans un ZIP structuré.
"""

import re
import zipfile
from io import BytesIO
from pathlib import Path


class DossierAssembler:
    """Assemble un dossier complet de candidature en ZIP."""

    def __init__(self, entreprise_nom: str, fonds_nom: str, intermediaire_nom: str | None = None):
        self.prefix = self._build_prefix(entreprise_nom, fonds_nom, intermediaire_nom)
        self.documents: list[tuple[str, bytes]] = []

    @staticmethod
    def _sanitize(name: str) -> str:
        clean = re.sub(r"[^\w\s-]", "", name)
        clean = re.sub(r"\s+", "_", clean.strip())
        return clean[:50]

    def _build_prefix(self, entreprise: str, fonds: str, intermediaire: str | None) -> str:
        parts = ["Dossier", self._sanitize(fonds)]
        if intermediaire:
            parts.append(self._sanitize(intermediaire))
        parts.append(self._sanitize(entreprise))
        return "_".join(parts)

    def add_document(self, filename: str, content: bytes) -> None:
        """Ajoute un document au dossier."""
        self.documents.append((filename, content))

    def add_from_path(self, filename: str, filepath: Path) -> None:
        """Ajoute un fichier existant au dossier."""
        if filepath.exists():
            self.documents.append((filename, filepath.read_bytes()))

    def assemble(self) -> bytes:
        """Crée le ZIP final."""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in self.documents:
                zf.writestr(f"{self.prefix}/{filename}", content)
        return buffer.getvalue()
