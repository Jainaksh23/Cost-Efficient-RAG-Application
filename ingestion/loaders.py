"""
ingestion/loaders.py
One loader function per supported file type.
Each returns (text: str, metadata: dict) where metadata contains:
  source_file   — basename of the original file
  file_type     — "pdf" | "html" | "md"
  ingested_at   — ISO-8601 UTC timestamp
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


# ── Internal helpers ──────────────────────────────────────────────────────────

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _meta(path: Path, file_type: str) -> dict:
    return {
        "source_file": path.name,          # basename only — path-agnostic
        "file_type":   file_type,
        "ingested_at": _now_utc(),
    }


# ── PDF loader (pypdf) ────────────────────────────────────────────────────────

def load_pdf(path: Path) -> tuple[str, dict]:
    """Extract plain text from a PDF using pypdf."""
    from pypdf import PdfReader  # deferred import — not needed for non-PDF runs

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            pages.append(extracted)

    text = "\n\n".join(pages).strip()
    return text, _meta(path, "pdf")


# ── HTML loader (BeautifulSoup) ───────────────────────────────────────────────

def load_html(path: Path) -> tuple[str, dict]:
    """Strip HTML tags and return clean plain text."""
    from bs4 import BeautifulSoup  # deferred import

    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "head", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Collapse runs of 3+ blank lines down to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), _meta(path, "html")


# ── Markdown loader ───────────────────────────────────────────────────────────

def load_md(path: Path) -> tuple[str, dict]:
    """Read a Markdown file as raw text (no stripping — chunker handles it)."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")  # strips BOM
    return text.strip(), _meta(path, "md")


# ── Dispatch ──────────────────────────────────────────────────────────────────

_LOADERS = {
    ".pdf":  load_pdf,
    ".html": load_html,
    ".htm":  load_html,
    ".md":   load_md,
}


def load_document(path: Path) -> tuple[str, dict]:
    """
    Load a document from disk and return (text, metadata).

    Raises:
        ValueError: if the file extension is not supported.
        FileNotFoundError: if the path does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    loader = _LOADERS.get(ext)
    if loader is None:
        raise ValueError(
            f"Unsupported file type {ext!r}. "
            f"Supported: {list(_LOADERS.keys())}"
        )

    return loader(path)
