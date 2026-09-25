"""Small helpers shared by the paper scripts. Python stdlib only."""
import json
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

MY_NAME = "Eli Ben-Michael"
USER_AGENT = "ebenmichael.github.io paper helper (mailto:ebenmichael@cmu.edu)"

# ---------------------------------------------------------------- remote metadata


def tidy(s):
    """LaTeX-style quotes -> typographic quotes."""
    return re.sub(r"``(.*?)''", "\u201c\\1\u201d", s)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def arxiv_fetch(ids):
    """Fetch metadata for arXiv ids. Returns {id: {title, authors, abstract, year}}."""
    ns = {"a": "http://www.w3.org/2005/Atom"}
    q = urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    root = ET.fromstring(_get(f"https://export.arxiv.org/api/query?{q}"))
    out = {}
    for e in root.findall("a:entry", ns):
        raw_id = e.findtext("a:id", "", ns)
        m = re.search(r"abs/([^v]+)(v\d+)?$", raw_id)
        if not m:
            continue
        ws = lambda s: re.sub(r"\s+", " ", s or "").strip()  # noqa: E731
        out[m.group(1)] = {
            "title": ws(e.findtext("a:title", "", ns)),
            "authors": [ws(a.findtext("a:name", "", ns)) for a in e.findall("a:author", ns)],
            "abstract": tidy(ws(e.findtext("a:summary", "", ns))),
            "year": int(e.findtext("a:published", "0000", ns)[:4]),
        }
    return out


def crossref_fetch(doi):
    """Fetch metadata for a DOI from Crossref."""
    msg = json.loads(_get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))["message"]
    year = None
    for k in ("published-print", "published-online", "issued"):
        parts = msg.get(k, {}).get("date-parts") or [[None]]
        if parts[0][0]:
            year = parts[0][0]
            break
    abstract = re.sub(r"<[^>]+>", " ", msg.get("abstract", ""))
    abstract = re.sub(r"\s+", " ", abstract).strip()
    abstract = re.sub(r"^Abstract\s*", "", abstract)
    authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in msg.get("author", [])]
    return {
        "title": re.sub(r"\s+", " ", (msg.get("title") or [""])[0]).strip(),
        "authors": authors,
        "venue": (msg.get("container-title") or [""])[0],
        "year": year,
        "abstract": abstract,
        "type": "chapter" if msg.get("type") == "book-chapter" else "article",
        "url": msg.get("URL", "https://doi.org/" + doi),
    }


# ---------------------------------------------------------------- papers.yml I/O

STOP = {"a", "an", "the", "on", "of", "for", "to", "in", "with", "and", "is", "using", "via"}


def make_id(authors, year, title, used):
    first = authors[0] if authors else MY_NAME
    last = unicodedata.normalize("NFKD", first.split()[-1]).encode("ascii", "ignore").decode()
    last = re.sub(r"[^a-z]", "", last.lower())
    words = [w for w in re.findall(r"[a-z0-9]+", title.lower()) if w not in STOP]
    base = f"{last}-{year or 'nd'}-{words[0] if words else 'paper'}"
    pid, n = base, 2
    while pid in used:
        pid = f"{base}-{n}"
        n += 1
    used.add(pid)
    return pid


def q(s):
    """Double-quoted YAML scalar."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


LINK_ORDER = ["journal", "proceedings", "publisher", "arxiv", "nber", "draft", "code", "slides"]


def dump_paper(p):
    lines = [f"- id: {p['id']}",
             f"  title: {q(p['title'])}",
             "  authors: [" + ", ".join(q(a) for a in p["authors"]) + "]",
             f"  type: {p['type']}",
             f"  venue: {q(p.get('venue', ''))}",
             f"  year: {p.get('year') or ''}"]
    if p.get("forthcoming"):
        lines.append("  forthcoming: true")
    lines.append("  topics: [" + ", ".join(p.get("topics", [])) + "]")
    links = p.get("links", {})
    if links:
        lines.append("  links:")
        for k in sorted(links, key=lambda k: LINK_ORDER.index(k) if k in LINK_ORDER else 99):
            lines.append(f"    {k}: {q(links[k])}")
    if p.get("extra_links"):
        lines.append("  extra_links:")
        for x in p["extra_links"]:
            lines.append(f"    - {{label: {q(x['label'])}, url: {q(x['url'])}}}")
    if p.get("award"):
        lines.append(f"  award: {q(p['award'])}")
    if p.get("doi"):
        lines.append(f"  doi: {q(p['doi'])}")
    if p.get("abstract"):
        lines.append("  abstract: >-")
        lines.append("    " + p["abstract"])
    return "\n".join(lines) + "\n"


HEADER = """\
# Every paper on the site. /research/ groups these by `type`
# (preprint | article | chapter | discussion), newest year first; ties keep file order.
#
# Add a paper:     make paper ARXIV=2607.14346 TOPICS=policy-learning   (or DOI=10.xxxx/yyyy)
# Mark published:  make published ID=<id> DOI=10.xxxx/yyyy
#
# Fields: id, title, authors (full list, in order), type, venue, year, forthcoming (renders
# "2026+"), topics (slugs from _data/topics.yml), links (journal, proceedings, publisher, arxiv,
# nber, draft, code, slides), extra_links (label/url pairs), award, doi, abstract.

"""


def dump_papers(papers):
    return HEADER + "\n".join(dump_paper(p) for p in papers)
