# Crawlers

Standalone crawler scripts, with Python dependencies managed by uv.
The uv environment requires Python 3.13 or newer.

```sh
uv sync --locked
# Run a script after checking its compatibility and required configuration:
uv run <script.py> [arguments]
```

Commit both `pyproject.toml` and `uv.lock` when changing dependencies with
`uv add` or `uv remove`. The lockfile records exact versions for reproducible
installation and vulnerability scanning; it does not certify that the legacy
scripts work with those versions or that their target websites still work.

## Dependency inventory

| Package | Used by |
| --- | --- |
| beautifulsoup4 | `allpic.py`, `ehentai.py` |
| requests | HTTP requests across the Python crawlers |
| gevent | Concurrent downloads in image crawlers |
| lxml | HTML parsing, including Beautiful Soup's `lxml` backend |
| cssselect | `lxml.cssselect.CSSSelector` in `4chan.py`, `douban/pic.py` |

## Compatibility work still required

- Some scripts still use Python 2 syntax or standard-library APIs such as
  `urllib.urlopen` and `xrange`. Installing dependencies
  does not migrate these scripts to Python 3.
- `4chan.py` imports a missing local `utils` module for `initlog`.
  An unrelated package named `utils` is deliberately not installed.
- External commands, service credentials and website compatibility need
  separate checks before running each script. No crawler is executed during
  environment setup.

## Download page images

```sh
uv run allpic.py https://example.com/page.html -o images
```

Downloads HTTP(S) images from `img` tags in the returned HTML, resolving
relative URLs against the final page URL and any HTML `base` element.
Supports `lazyload-src`, `data-src`, `file`, and `src`; duplicate URLs are
downloaded once and colliding filenames receive a numeric suffix.
Failed downloads cause a nonzero exit status. JavaScript-generated images,
`srcset`-only images, and embedded data URLs are not downloaded.
