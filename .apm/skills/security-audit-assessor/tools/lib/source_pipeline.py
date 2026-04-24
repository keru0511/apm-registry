#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.request
from typing import Any
from urllib.parse import urljoin


ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "source-profiles.json"
WORK_ROOT = ROOT / "work"


def load_profiles() -> list[dict[str, Any]]:
    return json.loads(PROFILE_PATH.read_text())


def get_profile(doc_id: str) -> dict[str, Any]:
    for item in load_profiles():
        if item["doc_id"] == doc_id:
            return item
    raise SystemExit(f"unknown doc_id: {doc_id}")


def ensure_parent(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def normalize_whitespace(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_tags(raw: str) -> str:
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"</p>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", "", raw)
    return normalize_whitespace(raw)


def extract_main_fragment(source: str) -> str:
    match = re.search(r'<main(?: class="[^"]*")?>(.*)</main>', source, re.S)
    if not match:
        raise SystemExit("main content block not found")
    fragment = match.group(1)
    main_content_match = re.search(r'<div class="container" id="mainContent">(.*)', fragment, re.S)
    if main_content_match:
        fragment = main_content_match.group(1)
    fragment = fragment.split('<div class="inquiry-box"', 1)[0]
    fragment = fragment.split('<div class="change-log-box"', 1)[0]
    fragment = fragment.split('<section class="change-log-box">', 1)[0]
    return fragment


def first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.S)
    if not match:
        return None
    return strip_tags(match.group(1))


def extract_li_entries(chunk: str, base_url: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for item_html in re.findall(r"<li\b[^>]*>(.*?)</li>", chunk, re.S):
        text = strip_tags(item_html)
        if not text:
            continue
        href_match = re.search(r'<a [^>]*href="([^"]+)"', item_html)
        entry = {"text": text}
        if href_match:
            entry["href"] = urljoin(base_url, href_match.group(1))
        entries.append(entry)
    return entries


def sanitize_block_html(chunk: str) -> str:
    chunk = re.sub(r"<img\b[^>]*>", "", chunk, flags=re.I)
    chunk = re.sub(r"<div\b[^>]*>\s*</div>", "", chunk, flags=re.I | re.S)
    chunk = re.sub(r"<a [^>]*>\s*</a>", "", chunk, flags=re.I | re.S)
    return chunk


def extract_text_lines(chunk: str) -> list[str]:
    chunk = sanitize_block_html(chunk)
    chunk = re.sub(r"</?(ul|ol|dl|div|section)[^>]*>", "\n", chunk, flags=re.I)
    chunk = re.sub(r"</?(li|p|dd|dt|h3|h4|h5|h6)[^>]*>", "\n", chunk, flags=re.I)
    chunk = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.I)
    text = strip_tags(chunk)
    lines = [normalize_whitespace(line) for line in text.splitlines()]
    return [line for line in lines if line]


def extract_link_items(chunk: str, base_url: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for href, raw_text in re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', chunk, re.S):
        text = strip_tags(raw_text)
        if not text:
            continue
        items.append({"text": text, "href": urljoin(base_url, href)})
    return items


def parse_def_lists(chunk: str, base_url: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for dl_html in re.findall(r'<dl class="def-list">(.*?)</dl>', chunk, re.S):
        title = first_match(r'<dt class="def-list__ttl">(.*?)</dt>', dl_html)
        if not title:
            continue
        dd_match = re.search(r'<dd class="def-list__desc">(.*?)</dd>', dl_html, re.S)
        dd_html = dd_match.group(1) if dd_match else ""
        items = extract_li_entries(dd_html, base_url)
        paragraphs = [
            strip_tags(p)
            for p in re.findall(r'<p class="article-txt[^"]*">(.*?)</p>', dd_html, re.S)
            if strip_tags(p)
        ]
        block: dict[str, Any] = {"type": "definition_list", "title": title}
        if items:
            block["items"] = items
        if paragraphs:
            block["paragraphs"] = paragraphs
        blocks.append(block)
    return blocks


def split_subsections(chunk: str) -> tuple[str, list[tuple[str, str]]]:
    matches = list(re.finditer(r"<h3[^>]*>(.*?)</h3>", chunk, re.S))
    if not matches:
        return chunk, []
    intro = chunk[: matches[0].start()]
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        heading = strip_tags(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(chunk)
        sections.append((heading, chunk[start:end]))
    return intro, sections


def parse_download_cards(chunk: str, base_url: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for card_html in re.findall(r'<div class="book-detail">(.*?)</div>\s*</div>', chunk, re.S):
        title = first_match(r'<p class="book-detail__ttl[^"]*">(.*?)</p>', card_html)
        if not title:
            continue
        groups = parse_def_lists(card_html, base_url)
        cards.append({"type": "resource_card", "title": title, "groups": groups})
    return cards


def split_h2_sections(fragment: str) -> tuple[str, list[tuple[str, str]]]:
    matches = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", fragment, re.S))
    if not matches:
        return fragment, []
    intro = fragment[: matches[0].start()]
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        heading = strip_tags(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(fragment)
        sections.append((heading, fragment[start:end]))
    return intro, sections


def extract_publications_detail(source: str) -> str:
    match = re.search(r'<div class="publications-detail">(.*?)(?:<div class="bs-callout bs-callout-danger" id="topicsCallout-lg"|</body>)', source, re.S)
    if not match:
        raise SystemExit("publications detail block not found")
    return match.group(1)


def extract_span_values(container_id: str, source: str, prefix: str) -> list[str]:
    del container_id
    pattern = rf'<span id="{re.escape(prefix)}\d+">(.*?)</span>'
    values = [strip_tags(value) for value in re.findall(pattern, source, re.S)]
    return [value for value in values if value and value != "None selected"]


def extract_link_entries_from_container(container_id: str, source: str) -> list[dict[str, str]]:
    container_match = re.search(rf'<span id=["\']{re.escape(container_id)}["\'][^>]*>(.*?)</span>', source, re.S)
    if not container_match:
        return []
    container_html = container_match.group(1)
    items: list[dict[str, str]] = []
    for href, raw_text in re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', container_html, re.S):
        text = strip_tags(raw_text)
        if not text:
            continue
        items.append({"text": text, "href": urljoin("https://csrc.nist.gov", href)})
    return items


def extract_paragraph_after_label(label: str, source: str) -> str | None:
    match = re.search(rf'<strong>{re.escape(label)}:</strong>\s*(.*?)<br', source, re.S)
    if not match:
        return None
    return strip_tags(match.group(1))


def extract_pub_planning_note(source: str) -> dict[str, Any] | None:
    date_match = re.search(r"<span id=['\"]pub-planning-note-date['\"]>(.*?)</span>", source, re.S)
    body_match = re.search(r"<span id=['\"]pub-planning-note['\"]>(.*?)</span>", source, re.S)
    if not body_match:
        return None
    body_html = body_match.group(1)
    lines = extract_text_lines(body_html)
    links = extract_link_items(body_html, "https://csrc.nist.gov")
    note: dict[str, Any] = {"items": lines}
    if date_match:
        note["date"] = strip_tags(date_match.group(1))
    if links:
        note["links"] = links
    return note


def extract_pub_abstract(source: str) -> str | None:
    match = re.search(r'<div[^>]*id="pub-detail-abstract-info"[^>]*>\s*<p>(.*?)</p>', source, re.S)
    if not match:
        return None
    return strip_tags(match.group(1))


def extract_publication_link(source: str) -> dict[str, str] | None:
    match = re.search(r'<a href="([^"]+)" id="pub-doi-link"[^>]*>(.*?)</a>', source, re.S)
    if not match:
        return None
    return {"text": strip_tags(match.group(2)), "href": urljoin("https://csrc.nist.gov", match.group(1))}


def extract_download_link(source: str) -> dict[str, str] | None:
    match = re.search(r'<a href="([^"]+)" id="pub-local-download-link"[^>]*>(.*?)</a>', source, re.S)
    if not match:
        return None
    return {"text": strip_tags(match.group(2)), "href": urljoin("https://csrc.nist.gov", match.group(1))}


def ipa_safe_website_section_id(heading: str) -> str:
    mapping = {
        "資料のダウンロード": "resource_downloads",
        "ウェブアプリケーションのセキュリティ実装（第1章の抜粋）": "chapter_1_excerpt",
        "参考情報": "reference_information",
        "謝辞": "acknowledgements",
        "脚注": "footnotes",
    }
    return mapping.get(heading, re.sub(r"[^a-z0-9]+", "_", heading.lower()).strip("_") or "section")


def ipa_nfr_grade_section_id(heading: str) -> str:
    mapping = {
        "機能／非機能要求の相違点と課題": "differences_and_challenges",
        "非機能要求グレードとは": "grade_2018_artifacts",
        "非機能要求グレード（初版）": "initial_release",
        "利用手順": "procedure",
        "「非機能要求グレード」の効果": "expected_effects",
        "非機能要求グレード2018ダウンロード": "grade_2018_downloads",
        "各種研修教材": "training_materials",
        "ユーザー企業の経営層向け非機能要求の読本「経営に活かすIT投資の最適化」": "executive_reader",
        "セミナー説明資料": "seminar_materials",
        "非機能要求グレード本体（英語版）": "english_release",
        "非機能要求グレード本体（中国語版）": "chinese_release",
        "活用事例集": "casebook",
        "関連情報": "related_information",
        "更新履歴": "change_log",
    }
    return mapping.get(heading, re.sub(r"[^a-z0-9]+", "_", heading.lower()).strip("_") or "section")


def ipa_requirements_guide_section_id(heading: str) -> str:
    mapping = {
        "概要": "overview",
        "ダウンロード": "download",
        "本ガイド内の要求項目に対する補足説明": "supplemental_notes",
        "ご意見、ご要望などの受付": "feedback",
        "お問い合わせ先": "contact",
        "関連リンク": "related_links",
    }
    return mapping.get(heading, re.sub(r"[^a-z0-9]+", "_", heading.lower()).strip("_") or "section")


def nist_publication_section_ids(doc_id: str) -> dict[str, str]:
    if doc_id == "nist-csf-2-0":
        return {
            "overview": "overview_and_components",
            "planning_note": "govern",
            "keywords": "profiles_and_tiers",
            "documentation": "reference_tool_and_quick_starts",
            "supplemental": "protect",
            "related_publications": "identify",
            "document_history": "recover",
        }
    if doc_id == "nist-sp-800-53-r5":
        return {
            "overview": "overview",
            "planning_note": "incident_and_recovery",
            "keywords": "risk_and_people",
            "control_families": "access_and_identity",
            "documentation": "audit_and_configuration",
            "supplemental": "acquisition_and_supply_chain",
            "related_publications": "data_and_system_protection",
            "document_history": "risk_and_people",
        }
    raise SystemExit(f"unknown NIST publication doc_id: {doc_id}")


def normalize_ipa_safe_website(source: str, profile: dict[str, Any]) -> dict[str, Any]:
    base_url = profile["canonical_url"]
    fragment = extract_main_fragment(source)
    title = first_match(r"<h1[^>]*>(.*?)</h1>", fragment)
    if not title:
        raise SystemExit("h1 not found in main content")

    intro_html, h2_sections = split_h2_sections(fragment)

    update_info = [
        strip_tags(p)
        for p in re.findall(r'<p class="article-txt article-txt--right">(.*?)</p>', intro_html, re.S)
        if strip_tags(p)
    ]

    intro_body = intro_html.split('<div class="def-list__wrap">', 1)[0]
    intro_paragraphs = []
    for p_html in re.findall(r'<p class="article-txt[^"]*">(.*?)</p>', intro_body, re.S):
        text = strip_tags(p_html)
        if text:
            intro_paragraphs.append(text)

    sections: list[dict[str, Any]] = [
        {
            "section_id": "purpose_scope",
            "heading": title,
            "source_heading": "導入と別冊構成",
            "blocks": (
                [{"type": "paragraph", "text": text} for text in intro_paragraphs]
                + parse_def_lists(intro_html, base_url)
            ),
        }
    ]

    for heading, chunk in h2_sections:
        if heading in {"お問い合わせ先", "更新履歴"}:
            continue
        section: dict[str, Any] = {
            "section_id": ipa_safe_website_section_id(heading),
            "heading": heading,
            "source_heading": heading,
            "blocks": [],
        }
        paragraphs = [
            strip_tags(p)
            for p in re.findall(r'<p class="article-txt[^"]*">(.*?)</p>', chunk, re.S)
            if strip_tags(p)
        ]
        for text in paragraphs:
            section["blocks"].append({"type": "paragraph", "text": text})

        if heading == "資料のダウンロード":
            section["blocks"].extend(parse_download_cards(chunk, base_url))
        else:
            section["blocks"].extend(parse_def_lists(chunk, base_url))
            links = extract_li_entries(chunk, base_url)
            if links:
                section["blocks"].append({"type": "link_list", "items": links})

        sections.append(section)

    return {
        "doc_id": profile["doc_id"],
        "title": title,
        "canonical_url": base_url,
        "source_kind": profile["source_kind"],
        "normalizer": "ipa-safe-website-v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "update_info": update_info,
        "sections": sections,
    }


def normalize_ipa_nfr_grade(source: str, profile: dict[str, Any]) -> dict[str, Any]:
    base_url = profile["canonical_url"]
    fragment = extract_main_fragment(source)
    title = first_match(r"<h1[^>]*>(.*?)</h1>", fragment)
    if not title:
        raise SystemExit("h1 not found in main content")

    intro_html, h2_sections = split_h2_sections(fragment)
    intro_paragraphs = extract_text_lines(intro_html)
    sections: list[dict[str, Any]] = [
        {
            "section_id": "purpose_and_positioning",
            "heading": title,
            "source_heading": "導入と位置付け",
            "blocks": [{"type": "text_lines", "items": intro_paragraphs}],
        }
    ]

    for heading, chunk in h2_sections:
        if heading == "更新履歴":
            continue
        intro_chunk, subchunks = split_subsections(chunk)
        blocks: list[dict[str, Any]] = []

        intro_lines = extract_text_lines(intro_chunk)
        if intro_lines:
            blocks.append({"type": "text_lines", "items": intro_lines})

        intro_links = extract_link_items(intro_chunk, base_url)
        if intro_links:
            blocks.append({"type": "link_list", "items": intro_links})

        for subheading, subchunk in subchunks:
            sub_block: dict[str, Any] = {
                "type": "subsection",
                "heading": subheading,
                "items": extract_text_lines(subchunk),
            }
            links = extract_link_items(subchunk, base_url)
            if links:
                sub_block["links"] = links
            blocks.append(sub_block)

        if not subchunks:
            links = extract_link_items(chunk, base_url)
            if links and not any(block.get("type") == "link_list" for block in blocks):
                blocks.append({"type": "link_list", "items": links})

        sections.append(
            {
                "section_id": ipa_nfr_grade_section_id(heading),
                "heading": heading,
                "source_heading": heading,
                "blocks": blocks,
            }
        )

    return {
        "doc_id": profile["doc_id"],
        "title": title,
        "canonical_url": base_url,
        "source_kind": profile["source_kind"],
        "normalizer": "ipa-nfr-grade-v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sections": sections,
    }


def normalize_ipa_requirements_guide(source: str, profile: dict[str, Any]) -> dict[str, Any]:
    base_url = profile["canonical_url"]
    fragment = extract_main_fragment(source)
    title = first_match(r"<h1[^>]*>(.*?)</h1>", fragment)
    if not title:
        raise SystemExit("h1 not found in main content")

    intro_html, h2_sections = split_h2_sections(fragment)
    intro_lines = extract_text_lines(intro_html)
    intro_links = extract_link_items(intro_html, base_url)
    intro_blocks: list[dict[str, Any]] = []
    if intro_lines:
        intro_blocks.append({"type": "text_lines", "items": intro_lines})
    if intro_links:
        intro_blocks.append({"type": "link_list", "items": intro_links})

    sections: list[dict[str, Any]] = [
        {
            "section_id": "introduction",
            "heading": title,
            "source_heading": "導入と別冊案内",
            "blocks": intro_blocks,
        }
    ]

    for heading, chunk in h2_sections:
        if heading in {"更新履歴", "お問い合わせ先"}:
            # contact is handled only if needed below; update history is maintenance-only.
            if heading == "お問い合わせ先":
                contact_lines = extract_text_lines(chunk)
                contact_links = extract_link_items(chunk, base_url)
                blocks: list[dict[str, Any]] = []
                if contact_lines:
                    blocks.append({"type": "text_lines", "items": contact_lines})
                if contact_links:
                    blocks.append({"type": "link_list", "items": contact_links})
                sections.append(
                    {
                        "section_id": "contact",
                        "heading": heading,
                        "source_heading": heading,
                        "blocks": blocks,
                    }
                )
            continue

        intro_chunk, subchunks = split_subsections(chunk)
        blocks: list[dict[str, Any]] = []

        intro_lines = extract_text_lines(intro_chunk)
        if intro_lines:
            blocks.append({"type": "text_lines", "items": intro_lines})

        intro_links = extract_link_items(intro_chunk, base_url)
        if intro_links:
            blocks.append({"type": "link_list", "items": intro_links})

        for subheading, subchunk in subchunks:
            sub_block: dict[str, Any] = {
                "type": "subsection",
                "heading": subheading,
                "items": extract_text_lines(subchunk),
            }
            links = extract_link_items(subchunk, base_url)
            if links:
                sub_block["links"] = links
            blocks.append(sub_block)

        sections.append(
            {
                "section_id": ipa_requirements_guide_section_id(heading),
                "heading": heading,
                "source_heading": heading,
                "blocks": blocks,
            }
        )

    return {
        "doc_id": profile["doc_id"],
        "title": title,
        "canonical_url": base_url,
        "source_kind": profile["source_kind"],
        "normalizer": "ipa-requirements-guide-v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sections": sections,
    }


def normalize_nist_publication(source: str, profile: dict[str, Any]) -> dict[str, Any]:
    fragment = extract_publications_detail(source)
    title = first_match(r'<h1 id="pub-title">(.*?)</h1>', fragment)
    if not title:
        raise SystemExit("pub-title not found in publications detail")
    header_display = first_match(r'<h3 id="pub-header-display-container">(.*?)</h3>', fragment)
    date_published = extract_paragraph_after_label("Date Published", fragment)
    abstract = extract_pub_abstract(fragment)
    planning_note = extract_pub_planning_note(fragment)
    authors = extract_span_values("pub-authors-container", fragment, "pub-author-")
    keywords = extract_span_values("pub-keywords-container", fragment, "pub-keyword-")
    control_families = extract_span_values("pub-control-fam-container", fragment, "pub-control-fam-")
    supplemental = extract_link_entries_from_container("pub-supp-container", fragment)
    related_publications = extract_link_entries_from_container("pub-related-container", fragment)
    publication_parts = extract_link_entries_from_container("pub-part-container", fragment)
    document_history = extract_text_lines(
        re.search(r'<span id="pub-history-container"[^>]*>(.*?)</span>', fragment, re.S).group(1)
    ) if re.search(r'<span id="pub-history-container"[^>]*>(.*?)</span>', fragment, re.S) else []

    publication_link = extract_publication_link(fragment)
    download_link = extract_download_link(fragment)
    section_ids = nist_publication_section_ids(profile["doc_id"])

    sections: list[dict[str, Any]] = []

    overview_items = [item for item in [header_display, date_published, abstract] if item]
    if authors:
        overview_items.extend([f"Author: {author}" for author in authors])
    sections.append(
        {
            "section_id": section_ids["overview"],
            "heading": title,
            "source_heading": "Publication overview",
            "blocks": [{"type": "text_lines", "items": overview_items}],
        }
    )

    if planning_note:
        blocks: list[dict[str, Any]] = []
        planning_items = planning_note.get("items", [])
        if planning_note.get("date"):
            planning_items = [f"Planning Note Date: {planning_note['date']}"] + planning_items
        if planning_items:
            blocks.append({"type": "text_lines", "items": planning_items})
        if planning_note.get("links"):
            blocks.append({"type": "link_list", "items": planning_note["links"]})
        sections.append(
            {
                "section_id": section_ids["planning_note"],
                "heading": "Planning Note",
                "source_heading": "Planning Note",
                "blocks": blocks,
            }
        )

    keyword_blocks: list[dict[str, Any]] = []
    if keywords:
        keyword_blocks.append({"type": "text_lines", "items": keywords})
    if control_families and "control_families" in section_ids:
        sections.append(
            {
                "section_id": section_ids["control_families"],
                "heading": "Control Families",
                "source_heading": "Control Families",
                "blocks": [{"type": "text_lines", "items": control_families}],
            }
        )
    elif control_families:
        keyword_blocks.append({"type": "text_lines", "items": control_families})
    if keyword_blocks:
        sections.append(
            {
                "section_id": section_ids["keywords"],
                "heading": "Keywords and Topics",
                "source_heading": "Keywords and Topics",
                "blocks": keyword_blocks,
            }
        )

    documentation_blocks: list[dict[str, Any]] = []
    publication_items = [item for item in [publication_link, download_link] if item]
    if publication_items:
        documentation_blocks.append({"type": "link_list", "items": publication_items})
    if publication_parts:
        documentation_blocks.append({"type": "link_list", "items": publication_parts})
    if documentation_blocks:
        sections.append(
            {
                "section_id": section_ids["documentation"],
                "heading": "Documentation",
                "source_heading": "Documentation",
                "blocks": documentation_blocks,
            }
        )

    if supplemental:
        sections.append(
            {
                "section_id": section_ids["supplemental"],
                "heading": "Supplemental Material",
                "source_heading": "Supplemental Material",
                "blocks": [{"type": "link_list", "items": supplemental}],
            }
        )

    if related_publications:
        sections.append(
            {
                "section_id": section_ids["related_publications"],
                "heading": "Related Publications",
                "source_heading": "Related Publications",
                "blocks": [{"type": "link_list", "items": related_publications}],
            }
        )

    if document_history:
        sections.append(
            {
                "section_id": section_ids["document_history"],
                "heading": "Document History",
                "source_heading": "Document History",
                "blocks": [{"type": "text_lines", "items": document_history}],
            }
        )

    return {
        "doc_id": profile["doc_id"],
        "title": title,
        "canonical_url": profile["canonical_url"],
        "source_kind": profile["source_kind"],
        "normalizer": f"{profile['doc_id']}-v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sections": sections,
    }


def normalize_source(doc_id: str, input_path: pathlib.Path, output_path: pathlib.Path) -> None:
    profile = get_profile(doc_id)
    if profile["doc_id"] == "ipa-safe-website":
        data = normalize_ipa_safe_website(input_path.read_text(), profile)
    elif profile["doc_id"] == "ipa-nfr-grade":
        data = normalize_ipa_nfr_grade(input_path.read_text(), profile)
    elif profile["doc_id"] == "ipa-requirements-guide":
        data = normalize_ipa_requirements_guide(input_path.read_text(), profile)
    elif profile["doc_id"] in {"nist-csf-2-0", "nist-sp-800-53-r5"}:
        data = normalize_nist_publication(input_path.read_text(), profile)
    else:
        raise SystemExit(f"normalize-source is not implemented for {doc_id} yet")
    ensure_parent(output_path)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def default_raw_path(doc_id: str) -> pathlib.Path:
    return WORK_ROOT / "raw" / f"{doc_id}.html"


def default_normalized_path(doc_id: str) -> pathlib.Path:
    return WORK_ROOT / "normalized" / f"{doc_id}.json"


def default_corpus_path(doc_id: str) -> pathlib.Path:
    return WORK_ROOT / "corpus" / f"{doc_id}.toon"


def fetch_source(doc_id: str, output_path: pathlib.Path) -> None:
    profile = get_profile(doc_id)
    ensure_parent(output_path)
    request = urllib.request.Request(
        profile["canonical_url"],
        headers={"User-Agent": "apm-registry security-audit-assessor source fetcher"},
    )
    with urllib.request.urlopen(request) as response:
        body = response.read().decode("utf-8")
    output_path.write_text(body)


def build_source_corpus(input_path: pathlib.Path, output_path: pathlib.Path) -> None:
    ensure_parent(output_path)
    subprocess.run(
        ["toon", "--encode", str(input_path), "--output", str(output_path)],
        check=True,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch")
    fetch_parser.add_argument("doc_id")
    fetch_parser.add_argument("--output")

    normalize_parser = subparsers.add_parser("normalize")
    normalize_parser.add_argument("doc_id")
    normalize_parser.add_argument("--input")
    normalize_parser.add_argument("--output")

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("doc_id")
    build_parser.add_argument("--input")
    build_parser.add_argument("--output")

    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("doc_id")
    refresh_parser.add_argument("--raw-output")
    refresh_parser.add_argument("--normalized-output")
    refresh_parser.add_argument("--corpus-output")

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.command == "fetch":
        output = pathlib.Path(args.output) if args.output else default_raw_path(args.doc_id)
        fetch_source(args.doc_id, output)
        print(output)
        return

    if args.command == "normalize":
        input_path = pathlib.Path(args.input) if args.input else default_raw_path(args.doc_id)
        output = pathlib.Path(args.output) if args.output else default_normalized_path(args.doc_id)
        normalize_source(args.doc_id, input_path, output)
        print(output)
        return

    if args.command == "build":
        input_path = pathlib.Path(args.input) if args.input else default_normalized_path(args.doc_id)
        output = pathlib.Path(args.output) if args.output else default_corpus_path(args.doc_id)
        build_source_corpus(input_path, output)
        print(output)
        return

    if args.command == "refresh":
        raw_output = pathlib.Path(args.raw_output) if args.raw_output else default_raw_path(args.doc_id)
        normalized_output = pathlib.Path(args.normalized_output) if args.normalized_output else default_normalized_path(args.doc_id)
        corpus_output = pathlib.Path(args.corpus_output) if args.corpus_output else default_corpus_path(args.doc_id)
        fetch_source(args.doc_id, raw_output)
        normalize_source(args.doc_id, raw_output, normalized_output)
        build_source_corpus(normalized_output, corpus_output)
        print(corpus_output)
        return

    parser.error("unsupported command")


if __name__ == "__main__":
    main()
