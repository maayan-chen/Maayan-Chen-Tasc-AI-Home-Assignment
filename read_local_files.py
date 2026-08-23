import hashlib
from pathlib import Path

from vector_store import ContentExtractionError, extract_content_from_bytes


def read_local_files(folder_path: str) -> list[tuple[str, str, str]]:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder_path}")

    results = []
    for p in folder.rglob("*"):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue

        raw_bytes = p.read_bytes()
        try:
            content = extract_content_from_bytes(raw_bytes, source=str(p))
        except ContentExtractionError as e:
            print(f"Skipped {p}: {e}")
            continue

        file_hash = hashlib.sha256(raw_bytes).hexdigest()
        results.append((content, str(p), file_hash))

    return results
