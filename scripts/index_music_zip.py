from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic"}


def index_archive(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path) as archive:
        screenshots = [
            info.filename
            for info in archive.infolist()
            if not info.is_dir()
            and not info.filename.startswith("__MACOSX/")
            and Path(info.filename).suffix.lower() in IMAGE_EXTENSIONS
        ]

    return {
        "source": str(zip_path),
        "screenshot_count": len(screenshots),
        "screenshots": screenshots,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index music-library screenshots from one or more ZIP archives."
    )
    parser.add_argument(
        "zip_paths",
        nargs="*",
        help="ZIP archives to index. If omitted, all *.zip files in the repo root are used.",
    )
    parser.add_argument("--output", default="data/library_manifest.json")
    args = parser.parse_args()

    zip_paths = [Path(path) for path in args.zip_paths]
    if not zip_paths:
        zip_paths = sorted(Path(".").glob("*.zip"))

    if not zip_paths:
        raise SystemExit("No ZIP archives found.")

    sources = [index_archive(path) for path in zip_paths]
    total = sum(source["screenshot_count"] for source in sources)

    payload = {
        "sources": sources,
        "source_count": len(sources),
        "screenshot_count": total,
        "status": "indexed-not-transcribed",
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"indexed {total} screenshots from {len(sources)} archives -> {output}")


if __name__ == "__main__":
    main()
