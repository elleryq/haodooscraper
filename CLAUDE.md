# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Scraper for http://www.haodoo.net (a Chinese e-book site) plus a small Flask web app/API for searching the scraped catalog. Python 3. There is no test suite, linter config, or build step.

## Commands

```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

python -m haodooscraper.scraper   # full scrape (WIPES all tables first, then re-scrapes)
python wsgi/application           # dev web server on 127.0.0.1:8000
```

Environment variables:
- `OPENSHIFT_MYSQL_DB_URL` — if set (e.g. `mysql://user:pass@host:3306/`, see `example.env`), uses MySQL via PyMySQL with database `haodooscraper` appended; otherwise falls back to `sqlite:///db.sqlite3` relative to the CWD.
- `OPENSHIFT_PYTHON_IP` / `OPENSHIFT_PYTHON_PORT` — web server bind address.
- `DEBUG` — Flask debug flag (`true`/`false`).

## Architecture

- `haodooscraper/model.py` — SQLAlchemy models and a **module-level global `engine`/`session`**, created on import; `Base.metadata.create_all` also runs at import time (no migrations are actually used, despite alembic in requirements). Tables:
  - `bookpages` (`Page`): one row per book page URL found on category listings.
  - `bookvolumes` (`Volume`): one row per downloadable volume; a page can contain multiple volumes. `bookid` links back to `Page.id` (by string, not a FK).
  - `volumeexts` (`VolumeExt`): download links per format (epub/updb/pdb/mobi), FK to `bookvolumes._id`.
  - Each model has an autoincrement `_id` PK plus a site-specific string `id`. Models extend flask_jsontools' `JsonSerializableBase`; `Volume.__json__` strips `_id` and embeds `exts`.
- `haodooscraper/scraper.py` — staged pipeline in `scrape_haodoo()`:
  1. Iterate hardcoded category URLs from `urls()` and their paginated sub-pages (`P=<cat>-1`, `-2`, … until a `<strong>404` page), saving book links (`M=book`/`M=Share` with `P=<id>`) as `Page` rows.
  2. Fetch every `Page` in parallel with `multiprocessing.Pool` and parse volumes in `analysis_book_html_and_save` (despite the name, it only returns dicts; it does not save). Two page layouts are handled: old-style pages with a direct `.pdb` link, and new-style pages where `<input type=button onclick="DownloadEpub('id')">` etc. are parsed — volume IDs are extracted from the onclick JS with `ast` (`find_volume_id_3`); the other `find_volume_id*`/`extract_set_title*` variants are older alternatives.
  3. Save volumes serially in the parent process (`save_volume`) — DB writes must stay out of the worker pool since they share the global session.
- `wsgi/` — Flask app (OpenShift-style layout). `wsgi/application` adds the repo root to `sys.path` and imports `routes` (which imports `restplus` as a top-level module, so run it from the script, not as a package). `/` renders a paginated search over `Volume` title/author; `/api/book/search/` is a flask-restplus endpoint (Swagger UI at `/api/`).
- `.openshift/cron/daily/scraper` — runs the scraper daily on the legacy OpenShift deployment.
- `get_haodoo_books.py` (untracked) — standalone downloader that reads `haodoo_books.json` (list of `{link, title, volumetype}`) and downloads each file with random delays.
- `view.py` — legacy Python 2 ScraperWiki view; not used by the current code.
