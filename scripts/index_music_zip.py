from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Index screenshot sources inside Music.zip.")
    parser.add_argument("zip_path", nargs="?", default="Music.zip")
    parser.add_argument("--output", default="data/library_manifest.json")
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    output = Path(args.output)
    with zipfile.ZipFile(zip_path) as archive:
        screenshots = [
            info.filename
            for info in archive.infolist()
            if not info.is_dir()
            and not info.filename.startswith("__MACOSX/")
            and Path(info.filename).suffix.lower() in IMAGE_EXTENSIONS
        ]

    payload = {
        "source": str(zip_path),
        "screenshot_count": len(screenshots),
        "screenshots": screenshots,
        "status": "indexed-not-transcribed",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"indexed {len(screenshots)} screenshots -> {output}")


if __name__ == "__main__":
    main()
