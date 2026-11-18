# haodooscraper

A Scraper to scrape http://www.haodoo.net

# Provides

 * A command-line tool to scrape haodoo.
 * Flask Web application to search/display scraped data.

# Requirements

* [uv](https://docs.astral.sh/uv/) (installs Python 3.12 automatically if needed)

# Installation

```
uv sync
```

# Run scraper

```
uv run python -m haodooscraper.scraper
```

# Web

```
uv run python wsgi/application
```
