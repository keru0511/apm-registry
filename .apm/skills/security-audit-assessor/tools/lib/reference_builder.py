#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

DEFAULT_PREFERRED_LIMIT = 3


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def decode_toon(toon_bin: str, toon_path: Path, output_dir: Path) -> dict:
    output_path = output_dir / f"{toon_path.name}.json"
    subprocess.run(
        [toon_bin, str(toon_path), "-o", str(output_path)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return load_json(output_path)


def dedupe_refs(items: list[dict], key_fields: tuple[str, ...]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        key = tuple(item[field] for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def preference_rank(preferences: list[str], value: str) -> int:
    try:
        return preferences.index(value)
    except ValueError:
        return len(preferences)


class CorpusIndexBuilder:
    def __init__(self, skill_root: Path, toon_bin: str):
        self.skill_root = skill_root
        self.references_root = skill_root / "references"
        self.index_root = self.references_root / "index"
        self.mappings_root = self.references_root / "mappings"
        self.policies_root = skill_root / "tools" / "policies"
        self.toon_bin = toon_bin

        self.document_policies = {
            item["doc_id"]: item for item in load_json(self.policies_root / "index" / "documents.json")
        }
        self.document_policy_order = list(self.document_policies)
        self.topic_policies = load_json(self.policies_root / "index" / "topics.json")
        self.alias_policies = load_json(self.policies_root / "index" / "aliases.json")
        self.mapping_policies = {
            "system-controls.json": load_json(self.policies_root / "mappings" / "system-controls.json"),
            "governance-controls.json": load_json(self.policies_root / "mappings" / "governance-controls.json"),
        }
        self.control_labels = {}
        for items in self.mapping_policies.values():
            for item in items:
                self.control_labels[item["control_id"]] = item["label"]

        self.docs = []
        self.docs_by_id = {}
        self.section_lookup = {}
        self.subsection_lookup = {}
        self.doc_order = {}
        self.topic_sections = defaultdict(list)
        self.topic_subsections = defaultdict(list)
        self.control_sections = defaultdict(list)
        self.control_subsections = defaultdict(list)

    def load_corpus(self) -> None:
        corpus_dir = self.references_root / "corpus"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            corpus_files = sorted(corpus_dir.glob("*.toon"))
            for path in corpus_files:
                data = decode_toon(self.toon_bin, path, tmp_dir)
                doc_id = data["doc_id"]
                self.docs.append(data)
                self.docs_by_id[doc_id] = data
                if doc_id in self.document_policies:
                    self.doc_order[doc_id] = self.document_policy_order.index(doc_id)
                else:
                    self.doc_order[doc_id] = len(self.document_policy_order) + len(self.doc_order)

                for section_index, section in enumerate(data["sections"]):
                    section_key = (doc_id, section["section_id"])
                    self.section_lookup[section_key] = {
                        "doc_id": doc_id,
                        "section_id": section["section_id"],
                        "title": section["title"],
                        "section_index": section_index,
                    }
                    for topic in section.get("topics", []):
                        self.topic_sections[topic].append(
                            {
                                "doc_id": doc_id,
                                "section_id": section["section_id"],
                                "title": section["title"],
                            }
                        )

                    for subsection_index, subsection in enumerate(section.get("subsections", [])):
                        subsection_key = (doc_id, section["section_id"], subsection["subsection_id"])
                        subsection_item = {
                            "doc_id": doc_id,
                            "section_id": section["section_id"],
                            "subsection_id": subsection["subsection_id"],
                            "title": subsection["source_heading"],
                            "section_index": section_index,
                            "subsection_index": subsection_index,
                        }
                        self.subsection_lookup[subsection_key] = subsection_item

                        for topic in subsection.get("topics", []):
                            self.topic_subsections[topic].append(
                                {
                                    "doc_id": doc_id,
                                    "section_id": section["section_id"],
                                    "subsection_id": subsection["subsection_id"],
                                    "title": subsection["source_heading"],
                                }
                            )
                            self.topic_sections[topic].append(
                                {
                                    "doc_id": doc_id,
                                    "section_id": section["section_id"],
                                    "title": section["title"],
                                }
                            )

                        for control_id in subsection.get("controls", []):
                            self.control_subsections[control_id].append(
                                {
                                    "doc_id": doc_id,
                                    "section_id": section["section_id"],
                                    "subsection_id": subsection["subsection_id"],
                                    "title": subsection["source_heading"],
                                }
                            )
                            self.control_sections[control_id].append(
                                {
                                    "doc_id": doc_id,
                                    "section_id": section["section_id"],
                                    "title": section["title"],
                                }
                            )

    def ref_sort_key(self, item: dict) -> tuple:
        doc_id = item["doc_id"]
        section_id = item["section_id"]
        section_index = self.section_lookup[(doc_id, section_id)]["section_index"]
        subsection_id = item.get("subsection_id")
        if subsection_id is None:
            return (self.doc_order[doc_id], section_index, -1, item.get("title", ""))
        subsection_index = self.subsection_lookup[(doc_id, section_id, subsection_id)]["subsection_index"]
        return (self.doc_order[doc_id], section_index, subsection_index, item.get("title", ""))

    def simplify_subsections(self, items: list[dict]) -> list[dict]:
        return [
            {
                "doc_id": item["doc_id"],
                "section_id": item["section_id"],
                "subsection_id": item["subsection_id"],
            }
            for item in items
        ]

    def rank_subsections(
        self,
        items: list[dict],
        *,
        preferred_documents: list[str] | None = None,
        preferred_topics: list[str] | None = None,
        preferred_controls: list[str] | None = None,
    ) -> list[dict]:
        preferred_documents = preferred_documents or []
        preferred_topics = preferred_topics or []
        preferred_controls = preferred_controls or []

        aggregated = {}
        for item in items:
            key = (item["doc_id"], item["section_id"], item["subsection_id"])
            if key not in aggregated:
                aggregated[key] = {
                    **item,
                    "_matched_topics": set(item.get("_matched_topics", [])),
                    "_matched_controls": set(item.get("_matched_controls", [])),
                }
                continue
            aggregated[key]["_matched_topics"].update(item.get("_matched_topics", []))
            aggregated[key]["_matched_controls"].update(item.get("_matched_controls", []))

        def sort_key(item: dict) -> tuple:
            matched_topics = item["_matched_topics"]
            matched_controls = item["_matched_controls"]
            matched_preferred_topics = matched_topics.intersection(preferred_topics)
            matched_preferred_controls = matched_controls.intersection(preferred_controls)

            return (
                preference_rank(preferred_documents, item["doc_id"]),
                0 if not preferred_controls or matched_preferred_controls else 1,
                -len(matched_preferred_controls),
                0 if not preferred_topics or matched_preferred_topics else 1,
                -len(matched_preferred_topics),
                *self.ref_sort_key(item),
            )

        ranked = sorted(aggregated.values(), key=sort_key)
        return [
            {key: value for key, value in item.items() if not key.startswith("_")}
            for item in ranked
        ]

    def filter_subsections(
        self,
        items: list[dict],
        *,
        allowed_documents: list[str] | None = None,
        excluded_documents: list[str] | None = None,
        required_topics: list[str] | None = None,
        required_controls: list[str] | None = None,
        excluded_subsections: list[str] | None = None,
    ) -> list[dict]:
        allowed_documents = set(allowed_documents or [])
        excluded_documents = set(excluded_documents or [])
        required_topics = set(required_topics or [])
        required_controls = set(required_controls or [])
        excluded_subsections = set(excluded_subsections or [])

        filtered = []
        for item in items:
            doc_id = item["doc_id"]
            subsection_ref = f"{doc_id}.{item['section_id']}.{item['subsection_id']}"
            matched_topics = set(item.get("_matched_topics", []))
            matched_controls = set(item.get("_matched_controls", []))

            if allowed_documents and doc_id not in allowed_documents:
                continue
            if doc_id in excluded_documents:
                continue
            if subsection_ref in excluded_subsections:
                continue
            if required_topics and not matched_topics.intersection(required_topics):
                continue
            if required_controls and not matched_controls.intersection(required_controls):
                continue

            filtered.append(item)
        return filtered

    def build_documents(self) -> tuple[list[dict], list[dict]]:
        documents = []
        standards = []
        for doc in sorted(self.docs, key=lambda item: self.doc_order[item["doc_id"]]):
            doc_id = doc["doc_id"]
            policy = self.document_policies[doc_id]
            section_ids = [section["section_id"] for section in doc["sections"]]
            subsection_count = sum(len(section["subsections"]) for section in doc["sections"])
            entry = {
                "doc_id": doc_id,
                "title": doc["title"],
                "publisher": doc["publisher"],
                "version": doc["version"],
                "publication_date": doc["publication_date"],
                "profiles": doc["profiles"],
                "canonical_url": doc["canonical_url"],
                "corpus_file": f"../corpus/{doc_id}.toon",
                "section_count": len(doc["sections"]),
                "subsection_count": subsection_count,
                "section_ids": section_ids,
                "keywords": policy["keywords"],
                "aliases": policy["aliases"],
            }
            documents.append(entry)
            standards.append(
                {
                    "id": doc_id,
                    "title": doc["title"],
                    "publisher": doc["publisher"],
                    "version": doc["version"],
                    "publication_date": doc["publication_date"],
                    "canonical_url": doc["canonical_url"],
                    "profiles": doc["profiles"],
                    "topics": policy["topics"],
                    "read_when": policy["read_when"],
                    "evidence_use": policy["evidence_use"],
                    "notes": policy["notes"],
                    "corpus_file": f"../corpus/{doc_id}.toon",
                    "section_ids": section_ids,
                    "keywords": policy["keywords"],
                    "aliases": policy["aliases"],
                }
            )
        return documents, standards

    def build_topics(self) -> list[dict]:
        result = []
        for policy in self.topic_policies:
            topic = policy["topic"]
            sections = dedupe_refs(
                sorted(self.topic_sections.get(topic, []), key=self.ref_sort_key),
                ("doc_id", "section_id"),
            )
            subsections = self.rank_subsections(
                [
                    {
                        **item,
                        "_matched_topics": [topic],
                    }
                    for item in self.topic_subsections.get(topic, [])
                ],
                preferred_documents=policy.get("preferred_documents", []),
            )
            subsections = dedupe_refs(subsections, ("doc_id", "section_id", "subsection_id"))
            preferred_subsections = subsections[: policy.get("max_results", DEFAULT_PREFERRED_LIMIT)]
            result.append(
                {
                    "topic": topic,
                    "aliases": policy["aliases"],
                    "sections": sections,
                    "subsections": subsections,
                    "preferred_subsections": self.simplify_subsections(preferred_subsections),
                }
            )
        return result

    def build_controls(self) -> list[dict]:
        policy_order = [
            item["control_id"]
            for file_name in ("system-controls.json", "governance-controls.json")
            for item in self.mapping_policies[file_name]
        ]
        result = []
        for control_id in policy_order:
            sections = dedupe_refs(
                sorted(self.control_sections.get(control_id, []), key=self.ref_sort_key),
                ("doc_id", "section_id"),
            )
            subsections = self.rank_subsections(
                [
                    {
                        **item,
                        "_matched_controls": [control_id],
                    }
                    for item in self.control_subsections.get(control_id, [])
                ],
            )
            subsections = dedupe_refs(subsections, ("doc_id", "section_id", "subsection_id"))
            result.append(
                {
                    "control_id": control_id,
                    "label": self.control_labels[control_id],
                    "sections": sections,
                    "subsections": subsections,
                    "preferred_subsections": self.simplify_subsections(
                        subsections[:DEFAULT_PREFERRED_LIMIT]
                    ),
                }
            )
        return result

    def build_aliases(self, topics: list[dict], controls: list[dict]) -> list[dict]:
        topic_map = {item["topic"]: item for item in topics}
        control_map = {item["control_id"]: item for item in controls}
        result = []
        for policy in self.alias_policies:
            subsection_items = []
            for topic in policy.get("topics", []):
                subsection_items.extend(
                    [
                        {
                            **item,
                            "_matched_topics": [topic],
                        }
                        for item in topic_map[topic]["subsections"]
                    ]
                )
            for control_id in policy.get("controls", []):
                subsection_items.extend(
                    [
                        {
                            **item,
                            "_matched_controls": [control_id],
                        }
                        for item in control_map[control_id]["subsections"]
                    ]
                )
            subsection_items = self.filter_subsections(
                subsection_items,
                allowed_documents=policy.get("allowed_documents", []),
                excluded_documents=policy.get("excluded_documents", []),
                required_topics=policy.get("must_have_topics", []),
                required_controls=policy.get("must_have_controls", []),
                excluded_subsections=policy.get("excluded_subsections", []),
            )
            subsections = self.rank_subsections(
                subsection_items,
                preferred_documents=policy.get("preferred_documents", []),
                preferred_topics=policy.get("preferred_topics", []),
                preferred_controls=policy.get("preferred_controls", []),
            )
            subsections = dedupe_refs(subsections, ("doc_id", "section_id", "subsection_id"))
            documents = []
            seen = set()
            for item in subsections:
                if item["doc_id"] in seen:
                    continue
                seen.add(item["doc_id"])
                documents.append(item["doc_id"])
            max_results = policy.get("max_results", DEFAULT_PREFERRED_LIMIT)
            preferred_subsections = self.simplify_subsections(subsections[:max_results])
            result.append(
                {
                    "query": policy["query"],
                    "topics": policy["topics"],
                    "controls": policy["controls"],
                    "documents": documents,
                    "subsections": self.simplify_subsections(subsections),
                    "preferred_subsections": preferred_subsections,
                    "max_results": max_results,
                    "search_hints": policy.get("notes", ""),
                }
            )
        return result

    def build_mappings(self, controls: list[dict]) -> dict[str, list[dict]]:
        controls_map = {item["control_id"]: item for item in controls}
        outputs = {}
        for file_name, policies in self.mapping_policies.items():
            items = []
            for policy in policies:
                refs = controls_map[policy["control_id"]]
                related_documents = []
                seen_docs = set()
                for section in refs["sections"]:
                    if section["doc_id"] in seen_docs:
                        continue
                    seen_docs.add(section["doc_id"])
                    related_documents.append(section["doc_id"])
                items.append(
                    {
                        **policy,
                        "related_documents": related_documents,
                        "related_sections": [
                            f"{item['doc_id']}.{item['section_id']}" for item in refs["sections"]
                        ],
                        "related_subsections": [
                            f"{item['doc_id']}.{item['section_id']}.{item['subsection_id']}"
                            for item in refs["subsections"]
                        ],
                    }
                )
            outputs[file_name] = items
        return outputs

    def generated_payload(self) -> dict[str, object]:
        self.load_corpus()
        documents, standards = self.build_documents()
        topics = self.build_topics()
        controls = self.build_controls()
        aliases = self.build_aliases(topics, controls)
        mappings = self.build_mappings(controls)
        return {
            "index/documents.json": documents,
            "index/security-standards.json": standards,
            "index/topics.json": topics,
            "index/controls.json": controls,
            "index/aliases.json": aliases,
            "mappings/system-controls.json": mappings["system-controls.json"],
            "mappings/governance-controls.json": mappings["governance-controls.json"],
        }

    def write_outputs(self) -> None:
        for rel_path, data in self.generated_payload().items():
            write_json(self.references_root / rel_path, data)

    def check_outputs(self) -> int:
        generated = self.generated_payload()
        mismatches = []
        for rel_path, data in generated.items():
            path = self.references_root / rel_path
            actual_text = path.read_text(encoding="utf-8")
            expected_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
            if actual_text != expected_text:
                mismatches.append(rel_path)
        if mismatches:
            for rel_path in mismatches:
                print(f"stale generated file: {rel_path}", file=sys.stderr)
            return 1
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild security audit reference indexes and mappings.")
    parser.add_argument("--check", action="store_true", help="fail if generated outputs differ from committed files")
    parser.add_argument(
        "--skill-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="security-audit-assessor skill root",
    )
    parser.add_argument("--toon-bin", default=shutil.which("toon") or "toon", help="toon CLI path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder = CorpusIndexBuilder(Path(args.skill_root), args.toon_bin)
    if args.check:
        return builder.check_outputs()
    builder.write_outputs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
