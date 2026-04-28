#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def decode_toon(toon_bin: str, toon_path: Path, output_dir: Path) -> dict:
    output_path = output_dir / f"{toon_path.name}.json"
    subprocess.run(
        [toon_bin, str(toon_path), "-o", str(output_path)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return load_json(output_path)


def encode_toon(toon_bin: str, data: dict, output_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        input_path = tmp_dir / f"{output_path.stem}.json"
        input_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        subprocess.run(
            [toon_bin, "--encode", str(input_path), "--output", str(output_path)],
            check=True,
            stdout=subprocess.DEVNULL,
        )


class AuditCorpusBuilder:
    def __init__(self, skill_root: Path, toon_bin: str):
        self.skill_root = skill_root
        self.toon_bin = toon_bin
        self.tools_root = skill_root / "tools"
        self.annotation_root = self.tools_root / "policies" / "annotations"
        self.source_root = self.tools_root / "work" / "corpus"
        self.output_root = skill_root / "references" / "corpus"

    def annotation_paths(self, doc_ids: list[str] | None) -> list[Path]:
        paths = sorted(self.annotation_root.glob("*.json"))
        if doc_ids is None:
            return paths
        wanted = set(doc_ids)
        return [path for path in paths if path.stem in wanted]

    def build_doc(self, annotation_path: Path) -> dict:
        annotation = load_json(annotation_path)
        doc_id = annotation["doc_id"]
        source_path = self.source_root / f"{doc_id}.toon"
        if not source_path.exists():
            raise SystemExit(f"source corpus not found: {source_path}")

        with tempfile.TemporaryDirectory() as tmp:
            source = decode_toon(self.toon_bin, source_path, Path(tmp))

        source_section_ids = {section["section_id"] for section in source.get("sections", [])}
        if not source_section_ids:
            raise SystemExit(f"{doc_id}: source corpus has no sections")

        sections = []
        for section in annotation["sections"]:
            for source_section_id in section.get("source_section_ids", []):
                if source_section_id not in source_section_ids:
                    raise SystemExit(f"{doc_id}: unknown source section {source_section_id}")

            built_subsections = []
            for subsection in section["subsections"]:
                built_subsections.append(
                    {
                        "subsection_id": subsection["subsection_id"],
                        "source_heading": subsection["source_heading"],
                        "topics": subsection["topics"],
                        "controls": subsection["controls"],
                        "key_points": subsection["key_points"],
                        "source_passages": subsection["source_passages"],
                    }
                )

            sections.append(
                {
                    "section_id": section["section_id"],
                    "section_number": section["section_number"],
                    "title": section["title"],
                    "source_heading": section["source_heading"],
                    "topics": section["topics"],
                    "text": section["text"],
                    "subsections": built_subsections,
                }
            )

        return {
            "doc_id": doc_id,
            "title": source["title"],
            "publisher": annotation["publisher"],
            "version": annotation["version"],
            "publication_date": annotation["publication_date"],
            "canonical_url": source["canonical_url"],
            "profiles": annotation["profiles"],
            "sections": sections,
        }

    def write_outputs(self, doc_ids: list[str] | None) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for annotation_path in self.annotation_paths(doc_ids):
                payload = self.build_doc(annotation_path)
                output_path = self.output_root / f"{payload['doc_id']}.toon"
                if output_path.exists():
                    actual = decode_toon(self.toon_bin, output_path, tmp_dir)
                    if actual == payload:
                        continue
                encode_toon(self.toon_bin, payload, output_path)

    def check_outputs(self, doc_ids: list[str] | None) -> int:
        mismatches: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for annotation_path in self.annotation_paths(doc_ids):
                payload = self.build_doc(annotation_path)
                actual_path = self.output_root / f"{payload['doc_id']}.toon"
                if not actual_path.exists():
                    mismatches.append(payload["doc_id"])
                    continue
                expected_path = tmp_dir / actual_path.name
                encode_toon(self.toon_bin, payload, expected_path)
                actual = decode_toon(self.toon_bin, actual_path, tmp_dir)
                expected = decode_toon(self.toon_bin, expected_path, tmp_dir)
                if actual != expected:
                    mismatches.append(payload["doc_id"])
        if mismatches:
            for doc_id in mismatches:
                print(f"stale promoted corpus: {doc_id}", file=sys.stderr)
            return 1
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote source corpora into audit corpora.")
    parser.add_argument(
        "--skill-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="security-audit-assessor skill root",
    )
    parser.add_argument("--toon-bin", default=shutil.which("toon") or "toon", help="toon CLI path")
    parser.add_argument("--check", action="store_true", help="fail if promoted outputs differ from committed files")
    parser.add_argument("--doc-id", action="append", help="limit promotion to a specific doc_id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder = AuditCorpusBuilder(Path(args.skill_root), args.toon_bin)
    if args.check:
        return builder.check_outputs(args.doc_id)
    builder.write_outputs(args.doc_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
