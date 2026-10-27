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
| beautifulsoup4 | `allpic.py`, `ehentai.py`, `77mh.py`, `cartoonmad.py`, `fin/lianjia.py` |
| requests | HTTP requests across the Python crawlers |
| gevent | Concurrent downloads in image crawlers and `twspider/run.py` |
| lxml | HTML parsing, including Beautiful Soup's `lxml` backend |
| cssselect | `lxml.cssselect.CSSSelector` in `4chan.py`, `pic.py`, `douban/pic.py` |
| html5lib | Beautiful Soup parser explicitly selected by `77mh.py` and `cartoonmad.py` |
| pandas | `fin/lianjia.py` |
| python-twitter | Provides `twitter.Api` / `GetUserTimeline` for `twspider/run.py` |
| redis | Redis client for `twspider/run.py`; a Redis server is separate |

## Compatibility work still required

- Some scripts still use Python 2 syntax or standard-library APIs such as
  `urllib2`, `urlparse`, `ConfigParser`, and `xrange`. Installing dependencies
  does not migrate these scripts to Python 3.
- `sfacg.py` imports Beautiful Soup 3 (`BeautifulSoup`). It must be migrated to
  `bs4`; Beautiful Soup 3 is not included in this Python 3 environment.
- `4chan.py` and `pic.py` import a missing local `utils` module for `initlog`.
  An unrelated package named `utils` is deliberately not installed.
- `77mh.js` and `artstation.js` use PhantomJS's built-in `webpage` and `system`
  modules, not npm dependencies. PhantomJS is not installed by uv.
- External commands, service credentials and website compatibility need
  separate checks before running each script. No crawler is executed during
  environment setup.
