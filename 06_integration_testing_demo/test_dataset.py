from contextlib import redirect_stdout
import csv
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_dataset_model_training/scripts"))
from validate_dataset import validate_dataset
from split_dataset import plan_split
from audit_images import audit_images


class DatasetTests(unittest.TestCase):
    def test_single_class_validation_and_background_images(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            root = Path(directory)
            for split in ("train", "val", "test"):
                (root / "images" / split).mkdir(parents=True)
                (root / "labels" / split).mkdir(parents=True)
                Image.new("RGB", (16, 16)).save(root / "images" / split / "image.jpg")
                (root / "labels" / split / "image.txt").write_text("0 0.5 0.5 0.2 0.2\n" if split != "test" else "")
            self.assertEqual(validate_dataset(root, verify_images=True), [])
            (root / "labels/train/image.txt").write_text("3 0.5 0.5 0.2 0.2\n")
            self.assertTrue(validate_dataset(root))

    def test_missing_dataset_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            self.assertTrue(validate_dataset(Path(directory)))

    def test_group_split_is_deterministic_and_keeps_sources_together(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "images").mkdir()
            (root / "labels").mkdir()
            groups = root / "groups.csv"
            with groups.open("w", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(["file", "group"])
                for group in range(10):
                    for index in range(2):
                        name = f"{group}_{index}"
                        (root / "images" / f"{name}.jpg").write_bytes(name.encode())
                        (root / "labels" / f"{name}.txt").write_text("")
                        writer.writerow([f"{name}.jpg", str(group)])
            first = plan_split(root, groups)
            self.assertEqual(first, plan_split(root, groups))
            self.assertEqual({split for _, split, _, _ in first}, {"train", "val", "test"})
            for group in range(10):
                self.assertEqual(len({split for name, split, _, _ in first if name == str(group)}), 1)

    def test_quality_audit_flags_duplicates_without_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (20, 20)).save(root / "dark.png")
            (root / "copy.png").write_bytes((root / "dark.png").read_bytes())
            result = audit_images(root)
            self.assertEqual(len(result), 2)
            self.assertTrue(any("Exact duplicate" in reason for item in result for reason in item["review_reasons"]))
            self.assertEqual(len(list(root.glob("*.png"))), 2)


if __name__ == "__main__":
    unittest.main()
