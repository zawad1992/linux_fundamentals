from __future__ import annotations

from pathlib import Path
import subprocess
from urllib.parse import quote


README_FILE = Path("README.md")
START_MARKER = "<!-- AUTO-INDEX-START -->"
END_MARKER = "<!-- AUTO-INDEX-END -->"
EXCLUDED_PREFIXES = (".github/",)
EXCLUDED_FILES = {"README.md"}


def get_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    files = []
    for line in result.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        normalized = path.replace("\\", "/")
        if normalized in EXCLUDED_FILES:
            continue
        if any(normalized.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue
        files.append(normalized)
    return sorted(files, key=str.lower)


def infer_description(path: Path) -> str:
    if path.suffix.lower() == ".md" and path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip().rstrip(".") + "."

    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    return (stem[:1].upper() + stem[1:] if stem else "Project file") + "."


def generate_table_rows(files: list[str]) -> list[str]:
    rows = ["| File | Description |", "| --- | --- |"]
    for file_path in files:
        desc = infer_description(Path(file_path))
        link_target = quote(file_path, safe="/._-")
        rows.append(f"| [{file_path}]({link_target}) | {desc} |")
    return rows


def update_readme() -> None:
    readme_text = README_FILE.read_text(encoding="utf-8")
    if START_MARKER not in readme_text or END_MARKER not in readme_text:
        raise RuntimeError("README is missing auto-index markers.")

    files = get_tracked_files()
    replacement = "\n".join([START_MARKER, *generate_table_rows(files), END_MARKER])

    before, remainder = readme_text.split(START_MARKER, 1)
    _, after = remainder.split(END_MARKER, 1)
    new_text = before + replacement + after
    README_FILE.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    update_readme()
