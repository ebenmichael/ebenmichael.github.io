#!/usr/bin/env python3
"""Add a paper to _data/papers.yml, pre-filled from arXiv or Crossref.

  python3 scripts/add_paper.py --arxiv 2607.14346 [--topics policy-learning,ai-llms]
  python3 scripts/add_paper.py --doi 10.1002/sim.70720
  python3 scripts/add_paper.py --published <id> --doi 10.xxxx/yyyy [--url https://...]

New entries go at the top of their section in the file (the site sorts by year, and
keeps file order within a year). Review the printed entry, then edit topics/venue as needed.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paperlib import arxiv_fetch, crossref_fetch, dump_paper, make_id, q  # noqa: E402

PAPERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_data", "papers.yml")
TOPICS = os.path.join(os.path.dirname(PAPERS), "topics.yml")


def split_blocks(text):
    parts = re.split(r"(?m)^(?=- id: )", text)
    return parts[0], parts[1:]


def block_field(block, name):
    m = re.search(rf"(?m)^  {name}: (.*)$", block)
    return m.group(1).strip() if m else None


def known_topics():
    return re.findall(r"(?m)^- slug: (\S+)", open(TOPICS, encoding="utf-8").read())


def check_topics(topics):
    bad = [t for t in topics if t not in known_topics()]
    if bad:
        sys.exit(f"Unknown topic(s): {', '.join(bad)}. Known: {', '.join(known_topics())}")


def insert(text, entry):
    """Insert before the first existing entry of the same type (or at the end)."""
    head, blocks = split_blocks(text)
    new = dump_paper(entry) + "\n"
    for i, b in enumerate(blocks):
        if block_field(b, "type") == entry["type"]:
            blocks.insert(i, new)
            break
    else:
        if blocks and not blocks[-1].endswith("\n\n"):
            blocks[-1] = blocks[-1].rstrip("\n") + "\n\n"
        blocks.append(new)
    return head + "".join(blocks)


def set_field(block, name, value_line, after="type"):
    """Replace `  name: ...` in block, or add it after the `after` field."""
    if re.search(rf"(?m)^  {name}:", block):
        return re.sub(rf"(?m)^  {name}: .*$", lambda _: f"  {name}: {value_line}", block, count=1)
    return re.sub(rf"(?m)^(  {after}: .*)$", lambda m: m.group(1) + f"\n  {name}: {value_line}", block, count=1)


def mark_published(text, pid, doi, url):
    head, blocks = split_blocks(text)
    for i, b in enumerate(blocks):
        if re.match(r"- id: (\S+)", b).group(1) != pid:
            continue
        meta = crossref_fetch(doi)
        url = url or meta["url"]
        b = set_field(b, "type", meta["type"])
        b = set_field(b, "venue", q(meta["venue"]))
        if meta["year"]:
            b = set_field(b, "year", str(meta["year"]))
        b = set_field(b, "doi", q(doi), after="topics")
        if re.search(r"(?m)^  links:$", b):
            if re.search(r"(?m)^    journal:", b):
                b = re.sub(r"(?m)^    journal: .*$", lambda _: f"    journal: {q(url)}", b)
            else:
                b = re.sub(r"(?m)^  links:$", lambda _: f"  links:\n    journal: {q(url)}", b)
        else:
            b = re.sub(r"(?m)^(  topics: .*)$", lambda m: m.group(1) + f"\n  links:\n    journal: {q(url)}", b, count=1)
        blocks[i] = b
        print(b)
        return head + "".join(blocks)
    sys.exit(f"No paper with id {pid!r} in {PAPERS}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arxiv", help="arXiv id, e.g. 2607.14346")
    ap.add_argument("--doi", help="DOI, e.g. 10.1002/sim.70720")
    ap.add_argument("--published", metavar="ID", help="mark an existing entry as published (needs --doi)")
    ap.add_argument("--url", help="journal URL (default: the DOI's landing page)")
    ap.add_argument("--topics", default="", help="comma-separated topic slugs")
    ap.add_argument("--dry-run", action="store_true", help="print the entry without writing")
    args = ap.parse_args()

    text = open(PAPERS, encoding="utf-8").read()

    if args.published:
        if not args.doi:
            sys.exit("--published needs --doi")
        text = mark_published(text, args.published, args.doi, args.url)
    else:
        if not (args.arxiv or args.doi):
            ap.error("give --arxiv and/or --doi")
        topics = [t.strip() for t in args.topics.split(",") if t.strip()]
        check_topics(topics)
        entry = {"topics": topics, "links": {}, "extra_links": []}
        if args.arxiv:
            aid = re.sub(r"^.*abs/|v\d+$", "", args.arxiv)
            meta = arxiv_fetch([aid]).get(aid)
            if not meta:
                sys.exit(f"arXiv id {aid} not found")
            entry.update(title=meta["title"], authors=meta["authors"], abstract=meta["abstract"],
                         year=meta["year"], type="preprint", venue="")
            entry["links"]["arxiv"] = aid
        if args.doi:
            meta = crossref_fetch(args.doi)
            entry.setdefault("title", meta["title"])
            entry.setdefault("authors", meta["authors"])
            if not entry.get("abstract"):
                entry["abstract"] = meta["abstract"]
            entry.update(type=meta["type"], venue=meta["venue"], doi=args.doi,
                         year=meta["year"] or entry.get("year"))
            entry["links"]["journal"] = args.url or meta["url"]
        if re.search(r"(?m)^  title: " + re.escape(q(entry["title"])) + "$", text):
            sys.exit(f"Already in papers.yml: {entry['title']}")
        used = set(re.findall(r"(?m)^- id: (\S+)", text))
        entry["id"] = make_id(entry["authors"], entry["year"], entry["title"], used)
        print(dump_paper(entry))
        text = insert(text, entry)

    if args.dry_run:
        print("(dry run: nothing written)")
        return
    with open(PAPERS, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Updated {os.path.relpath(PAPERS)}. Check venue/topics, then `make serve` to preview.")


if __name__ == "__main__":
    main()
