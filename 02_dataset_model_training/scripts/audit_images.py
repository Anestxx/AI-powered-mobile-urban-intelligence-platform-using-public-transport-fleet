"""Write a non-destructive image quality and duplicate review report."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageFilter, ImageStat


def audit_images(directory):
    seen = {}
    results = []
    for path in sorted(directory.rglob("*")):
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            continue
        item = {"file": str(path.relative_to(directory)), "review_reasons": []}
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in seen:
                item["review_reasons"].append(f"Exact duplicate of {seen[digest]}")
            seen.setdefault(digest, item["file"])
            with Image.open(path) as image:
                gray = image.convert("L").resize((256, 256))
                brightness = ImageStat.Stat(gray).mean[0]
                edge_strength = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES).crop((1, 1, 255, 255))).mean[0]
            item.update(brightness=round(brightness, 2), edge_strength=round(edge_strength, 2))
            if brightness < 20:
                item["review_reasons"].append("Very dark image")
            if edge_strength < 3:
                item["review_reasons"].append("Low edge detail: review for blur or uniform scene")
        except (OSError, ValueError) as exc:
            item["review_reasons"].append(f"Unreadable image: {exc}")
        results.append(item)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not args.images.is_dir():
        parser.error("Image directory does not exist")
    results = audit_images(args.images)
    if not results:
        parser.exit(1, "No images found\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"heuristic_review_only": True, "items": results}, indent=2), encoding="utf-8")
    print(f"Reviewed {len(results)} images; {sum(bool(item['review_reasons']) for item in results)} need review. Original files are unchanged.")


if __name__ == "__main__":
    main()
