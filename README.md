# ebenmichael.github.io

Source for https://ebenmichael.github.io — a small Jekyll site with no theme gem.
Pushing to `master` builds and deploys it with GitHub Actions (`.github/workflows/pages.yml`).

## Everyday tasks

| Task | Command |
| --- | --- |
| Preview locally | `make serve` → http://localhost:4000 |
| Add a paper from arXiv | `make paper ARXIV=2607.14346 TOPICS=policy-learning` |
| Add a paper from a DOI | `make paper DOI=10.1002/sim.70720` |
| Preprint got published | `make published ID=<paper id> DOI=10.xxxx/yyyy` |
| Update the CV PDF | `make cv` (copies `~/jobs/resume/ebm_cv.pdf`) |

After `make paper`, open `_data/papers.yml` and check the new entry: venue name,
topics, links, and any `extra_links` (press coverage etc.). Then commit and push.

## Where things live

- `_data/papers.yml` — every paper (the research page and home page render from this)
- `_data/topics.yml` — topic tags and their labels (order = filter chip order)
- `_data/software.yml`, `_data/navigation.yml`
- `index.md` (bio), `teaching.md`, `research.html`, `betty-ww2.md` (unlisted)
- `_layouts/`, `_includes/`, `assets/css/main.scss`, `assets/js/papers.js` — the theme
- `scripts/add_paper.py` — arXiv / Crossref helper behind `make paper`
