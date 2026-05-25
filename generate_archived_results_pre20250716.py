#!/usr/bin/env python3
"""
generate_archived_results_pre20250716.py
========================================
Download pre-website VarAC Wednesday results from the VikingNation.github.io
Jekyll blog and create standalone archived HTML pages for each week.

Covers: May 7, 2025 – July 9, 2025  (Weeks #1-#10)
        These are the 10 events that pre-date the varacwednesday.net site,
        which launched on July 16, 2025 (Week #11).

Source repo : https://github.com/VikingNation/VikingNation.github.io
Posts path  : _posts/varacWed/
Original URL: https://k3jsj.net/varacWed/ (index page)
              https://k3jsj.net/{title}/   (individual post, Jekyll /:title/ permalink)

What this script does
---------------------
1. For each of the 10 results posts, download the raw Markdown from GitHub.
2. Parse the YAML front matter (title, date).
3. Query the GitHub Commits API to get the most recent commit hash for the file.
4. Convert the Markdown body to an HTML fragment (simple paragraph wrapping;
   any existing <em>/<a> tags in the source are preserved verbatim).
5. Wrap in a self-contained HTML page styled to match the Jekyll Now theme
   used by k3jsj.net.
6. Save each page to archived-results/ with week-numbered filenames.
7. Prepend a new section to archived-results/index.html listing these pages
   with the same column layout (Event Date | Week | Repository | Git Commit | Tag).
   Column 3 (Repository) links to https://github.com/VikingNation/VikingNation.github.io.
"""

import urllib.request
import urllib.error
import ssl
import re, os, json, time, sys
from datetime import datetime

# Build an unverified SSL context — safe for fetching public GitHub raw content
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode    = ssl.CERT_NONE

# ── constants ─────────────────────────────────────────────────────────────────
REPO_OWNER = 'VikingNation'
REPO_NAME  = 'VikingNation.github.io'
BRANCH     = 'master'
REPO_URL   = f'https://github.com/{REPO_OWNER}/{REPO_NAME}'
RAW_BASE   = (f'https://raw.githubusercontent.com'
              f'/{REPO_OWNER}/{REPO_NAME}/{BRANCH}')
API_BASE   = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'

REPO_DIR   = (r'C:\Users\admin\OneDrive\Documents\HamRadio'
              r'\projects\www-varACWednesday')
OUTPUT_DIR = os.path.join(REPO_DIR, 'archived-results')
INDEX_HTML = os.path.join(OUTPUT_DIR, 'index.html')

# ── the 10 results posts (oldest first) ──────────────────────────────────────
WEEKS = [
    {'week': 1,  'event': '5/7/2025',   'display': 'May 7, 2025',
     'fn': '2025-05-07-VarACWedResults_May7_2025.md',
     'out': 'week-01-2025-05-07.html'},
    {'week': 2,  'event': '5/14/2025',  'display': 'May 14, 2025',
     'fn': '2025-05-14-VarACWedResults_May14_2025.md',
     'out': 'week-02-2025-05-14.html'},
    {'week': 3,  'event': '5/21/2025',  'display': 'May 21, 2025',
     'fn': '2025-05-21-VarACWedResults_May21_2025.md',
     'out': 'week-03-2025-05-21.html'},
    {'week': 4,  'event': '5/28/2025',  'display': 'May 28, 2025',
     'fn': '2025-05-28-VaraCWedResults_May28_2025.md',
     'out': 'week-04-2025-05-28.html'},
    {'week': 5,  'event': '6/4/2025',   'display': 'June 4, 2025',
     'fn': '2025-06-04-25-VarACWedresults_June4_2025.md',
     'out': 'week-05-2025-06-04.html'},
    {'week': 6,  'event': '6/11/2025',  'display': 'June 11, 2025',
     'fn': '2025-06-11-VaraCWedResults_June11_2025.md',
     'out': 'week-06-2025-06-11.html'},
    {'week': 7,  'event': '6/18/2025',  'display': 'June 18, 2025',
     'fn': '2025-06-18-VaraCWedResults_June18_2025.md',
     'out': 'week-07-2025-06-18.html'},
    {'week': 8,  'event': '6/25/2025',  'display': 'June 25, 2025',
     'fn': '2025-06-25-VaraCWedResults_June25_2025.md',
     'out': 'week-08-2025-06-25.html'},
    {'week': 9,  'event': '7/2/2025',   'display': 'July 2, 2025',
     'fn': '2025-07-02-VaraCWedResults_July2_2025.md',
     'out': 'week-09-2025-07-02.html'},
    {'week': 10, 'event': '7/9/2025',   'display': 'July 9, 2025',
     'fn': '2025-07-10-VarACWedResults_July9_2025.md',
     'out': 'week-10-2025-07-09.html'},
]

# ── Jekyll Now-inspired CSS (matches k3jsj.net visual style) ─────────────────
JEKYLL_NOW_CSS = """
  * { box-sizing: border-box; }
  html { font-size: 100%; }
  body {
    background: #fff;
    font: 18px/1.4 'Helvetica Neue', Helvetica, Arial, sans-serif;
    color: #333;
    margin: 0; padding: 0;
  }
  .container { margin: 0 auto; max-width: 740px; padding: 0 10px; width: 100%; }
  h1, h2, h3, h4, h5, h6 {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-weight: bold; color: #222;
    line-height: 1.7; margin: 1em 0 15px; padding: 0;
  }
  h1 { font-size: 30px; } h2 { font-size: 24px; } h3 { font-size: 20px; }
  a { color: #049be5; text-decoration: none; }
  a:hover { color: #049be5; text-decoration: underline; }
  em, i { font-style: italic; } strong, b { font-weight: bold; }
  img { max-width: 100%; }
  p { margin: 15px 0; }
  hr { border: 0; border-top: 1px solid #eee; margin: 1.5em 0; }

  /* ── masthead ── */
  .wrapper-masthead { margin-bottom: 50px; }
  .masthead {
    padding: 20px 0; border-bottom: 1px solid #eee;
    overflow: hidden;
  }
  .site-avatar { float: left; width: 70px; height: 70px; margin-right: 15px; }
  .site-avatar img { border-radius: 5px; }
  .site-info { float: left; }
  .site-name { margin: 0; font-size: 28px; letter-spacing: 1px; }
  .site-name a { color: #494949; }
  .site-description { margin: -5px 0 0 0; color: #666; font-size: 16px; }
  nav {
    float: right; margin-top: 23px;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 18px;
  }
  nav a { margin-left: 20px; color: #333; font-weight: 300; letter-spacing: 1px; }

  /* ── post ── */
  #main { padding: 0 0 40px; }
  .post h1 { font-size: 1.7em; }
  .post .entry { font-size: 16px; line-height: 1.8; }
  .post .date { font-style: italic; color: #666; margin-top: 10px; font-size: 14px; }

  /* ── footer ── */
  .wrapper-footer {
    margin-top: 50px; border-top: 1px solid #ddd; background-color: #eee;
  }
  footer { padding: 20px 0; text-align: center; font-size: 14px; color: #666; }
  footer a { color: #049be5; }

  /* ── archive notice banner ── */
  .archive-notice {
    background: #fff8e1; border: 1px solid #ffe082;
    border-radius: 4px; padding: 10px 16px;
    font-size: 14px; color: #555; margin-bottom: 20px;
  }
  .archive-notice a { color: #049be5; }
"""

# ── HTTP helpers ──────────────────────────────────────────────────────────────
HEADERS = {
    'User-Agent': 'VarAC-Wednesday-Archiver/1.0 (K3JSJ archive project)',
    'Accept':     'application/vnd.github.v3+json',
}

def fetch_url(url, retries=3):
    """GET a URL, return decoded string or None on failure."""
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code} on {url} (attempt {attempt})")
            if e.code == 404:
                return None
        except Exception as e:
            print(f"    Error fetching {url}: {e} (attempt {attempt})")
        if attempt < retries:
            time.sleep(2)
    return None

def fetch_json(url):
    raw = fetch_url(url)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"    JSON decode error for {url}: {e}")
    return None

# ── front-matter parser ───────────────────────────────────────────────────────
FM_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

def parse_front_matter(raw):
    """Return (metadata_dict, body_string) from a Jekyll/YAML front-matter file."""
    m = FM_RE.match(raw)
    if not m:
        return {}, raw
    fm_block = m.group(1)
    body     = raw[m.end():]
    meta     = {}
    for line in fm_block.splitlines():
        kv = line.split(':', 1)
        if len(kv) == 2:
            k = kv[0].strip()
            v = kv[1].strip().strip('"').strip("'")
            meta[k] = v
    return meta, body

# ── Markdown → HTML (lightweight, preserves inline HTML) ─────────────────────
def md_to_html(text):
    """
    Convert the simple Markdown used in these posts to HTML.
    Preserves any existing HTML tags.  Handles:
      - Blank-line paragraph boundaries
      - ## / ### headings
      - Lines starting with * or - as list items
      - Inline **bold**, *italic*, `code`
    """
    # Normalise line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Process inline markup
    def inline(s):
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         s)
        s = re.sub(r'`(.+?)`',       r'<code>\1</code>',     s)
        # Bare URLs not already in an href
        s = re.sub(
            r'(?<!=")(?<!=\')(https?://[^\s<>"]+)',
            lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>',
            s
        )
        return s

    paragraphs = re.split(r'\n{2,}', text.strip())
    html_parts = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        lines = para.splitlines()

        # Heading: ## or ###
        if re.match(r'^#{1,6}\s', lines[0]):
            level  = len(re.match(r'^(#+)', lines[0]).group(1))
            content = re.sub(r'^#+\s*', '', lines[0])
            html_parts.append(f'<h{level}>{inline(content)}</h{level}>')
            continue

        # Unordered list block: lines starting with * or -
        if all(re.match(r'^[*\-]\s', l) for l in lines if l.strip()):
            items = ''.join(
                f'<li>{inline(re.sub(r"^[*\-]\s+", "", l))}</li>'
                for l in lines if l.strip()
            )
            html_parts.append(f'<ul>{items}</ul>')
            continue

        # Horizontal rule: --- or ***
        if re.match(r'^[-*]{3,}$', para.strip()):
            html_parts.append('<hr>')
            continue

        # Regular paragraph: join lines with <br> only if single line,
        # otherwise join with space (the posts use single paragraphs).
        joined = ' '.join(l.rstrip() for l in lines)
        html_parts.append(f'<p>{inline(joined)}</p>')

    return '\n'.join(html_parts)

# ── GitHub Commits API: get latest commit hash for a file ────────────────────
def get_commit_hash(filepath_in_repo):
    """
    Return the short (8-char) and full commit hash of the most recent
    commit that touched filepath_in_repo, or (None, None) if unavailable.
    """
    url  = (f'{API_BASE}/commits'
            f'?path={urllib.request.quote(filepath_in_repo)}'
            f'&per_page=1&sha={BRANCH}')
    data = fetch_json(url)
    if data and isinstance(data, list) and data:
        full = data[0].get('sha', '')
        return full[:8], full
    return None, None

# ── standalone HTML builder ───────────────────────────────────────────────────
def build_page(title, post_date_str, body_html, commit_short, filepath):
    """Return a complete standalone HTML document."""
    original_url = (f'https://k3jsj.net/'
                    + re.sub(r'[^a-z0-9]+', '-',
                             title.lower()).strip('-')
                    + '/')
    gh_file_url = f'{REPO_URL}/blob/{BRANCH}/{filepath}'
    gh_commit_url = (f'{REPO_URL}/commit/{commit_short}'
                     if commit_short else '#')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title} &ndash; Jason Johnson K3JSJ</title>
  <!--
    Archived from: {gh_file_url}
    Commit       : {commit_short or 'unknown'}
    Original URL : {original_url}
  -->
  <style>
{JEKYLL_NOW_CSS}
  </style>
</head>
<body>

  <div class="wrapper-masthead">
    <div class="container">
      <header class="masthead">
        <div class="site-info">
          <h1 class="site-name">
            <a href="https://k3jsj.net">Jason Johnson</a>
          </h1>
          <p class="site-description">Ham Radio operator</p>
        </div>
        <nav>
          <a href="https://k3jsj.net/">Blog</a>
          <a href="https://k3jsj.net/varacWed/">VaracWed</a>
          <a href="index.html">Archive Index</a>
        </nav>
      </header>
    </div>
  </div>

  <div id="main" role="main">
    <div class="container">
      <div class="archive-notice">
        <strong>Archived page.</strong>
        Originally published at <a href="{original_url}" target="_blank">{original_url}</a>
        &mdash; source: <a href="{gh_file_url}" target="_blank">GitHub</a>
        (commit <a href="{gh_commit_url}" target="_blank">{commit_short or 'unknown'}</a>).
      </div>
      <article class="post">
        <h1>{title}</h1>
        <div class="entry">
{body_html}
        </div>
        <div class="date">Written on {post_date_str}</div>
      </article>
    </div>
  </div>

  <div class="wrapper-footer">
    <div class="container">
      <footer class="footer">
        Archived from
        <a href="https://k3jsj.net">k3jsj.net</a> &mdash;
        source repo:
        <a href="{REPO_URL}" target="_blank">{REPO_OWNER}/{REPO_NAME}</a>
      </footer>
    </div>
  </div>

</body>
</html>"""

# ── index.html updater ────────────────────────────────────────────────────────
def update_index(new_rows_html):
    """
    Prepend new_rows_html (a string of <tr> elements) into the existing
    index.html table, immediately after the <tr><th>…</th></tr> header row.
    Also adds a section heading above the new rows and the existing rows.
    """
    if not os.path.exists(INDEX_HTML):
        print(f"  WARNING: {INDEX_HTML} not found – skipping index update.")
        return

    with open(INDEX_HTML, encoding='utf-8') as fh:
        content = fh.read()

    # Insert new rows right after the header <tr>
    HEADER_ROW = ('<tr><th>Event Date</th><th>Week</th>'
                  '<th>Repository</th><th>Git Commit</th><th>Tag</th></tr>')
    SECTION_PRE  = ('\n    <!-- PRE-WEBSITE RESULTS (Weeks 1-10, k3jsj.net) -->\n'
                    '    <tr><td colspan="5" style="background:#e8f4e8;font-weight:bold;'
                    'padding:.5rem .9rem;">'
                    'Pre-website era &mdash; hosted on k3jsj.net '
                    '(May 7 &ndash; July 9, 2025, Weeks #1&ndash;#10)'
                    '</td></tr>\n')
    SECTION_POST = ('\n    <!-- VARACWEDNESDAY.NET RESULTS (Weeks 11+) -->\n'
                    '    <tr><td colspan="5" style="background:#e8eef8;font-weight:bold;'
                    'padding:.5rem .9rem;">'
                    'varacwednesday.net era &mdash; hosted on varacwednesday.net '
                    '(July 16, 2025 onward, Weeks #11&ndash;#32)'
                    '</td></tr>\n')

    insertion = SECTION_PRE + new_rows_html + SECTION_POST

    if HEADER_ROW in content:
        updated = content.replace(
            HEADER_ROW,
            HEADER_ROW + insertion,
            1   # replace only first occurrence
        )
        with open(INDEX_HTML, 'w', encoding='utf-8') as fh:
            fh.write(updated)
        print(f"  index.html updated: pre-website rows inserted.")
    else:
        print("  WARNING: Expected table header row not found in index.html.")
        print("           New rows were NOT inserted – check index.html manually.")

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print('=' * 72)
    print('VarAC Wednesday Pre-20250716 Results Archiver')
    print('=' * 72)
    print(f'Source : {REPO_URL}/_posts/varacWed/')
    print(f'Output : {OUTPUT_DIR}')
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    new_index_rows = ''
    results = []

    for wk in WEEKS:
        filepath = f'_posts/varacWed/{wk["fn"]}'
        raw_url  = f'{RAW_BASE}/{filepath}'

        print(f'Week #{wk["week"]:>2}  {wk["display"]}')
        print(f'  Fetching: {raw_url}')

        raw = fetch_url(raw_url)
        if raw is None:
            print(f'  ERROR: Could not download {wk["fn"]} – skipping.')
            continue

        meta, body = parse_front_matter(raw)
        title      = meta.get('title', f'Results - VarAC Wednesday {wk["display"]}')
        date_str   = meta.get('date',  wk['event'])
        # Format date nicely
        try:
            dt       = datetime.strptime(str(date_str).strip(), '%Y-%m-%d')
            date_fmt = dt.strftime('%B %-d, %Y')   # e.g. "May 7, 2025"
        except Exception:
            try:
                dt       = datetime.strptime(str(date_str).strip(), '%Y-%m-%d %H:%M:%S %z')
                date_fmt = dt.strftime('%B %-d, %Y')
            except Exception:
                date_fmt = wk['display']

        # Get commit hash from GitHub API
        print(f'  Fetching commit hash from GitHub API ...')
        short_hash, full_hash = get_commit_hash(filepath)
        print(f'  Commit: {short_hash or "unknown"}')
        time.sleep(0.5)   # be polite to the API

        # Convert body to HTML
        body_html = md_to_html(body)

        # Build standalone page
        page_html = build_page(title, date_fmt, body_html, full_hash, filepath)

        out_path = os.path.join(OUTPUT_DIR, wk['out'])
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(page_html)
        print(f'  Written: {wk["out"]}')

        # Build index row
        repo_link   = (f'<a href="{REPO_URL}" target="_blank">'
                       f'{REPO_OWNER}/{REPO_NAME}</a>')
        commit_link = (f'<a href="{REPO_URL}/commit/{full_hash}" target="_blank">'
                       f'{short_hash}</a>'
                       if full_hash
                       else short_hash or 'unknown')
        new_index_rows += (
            f'    <tr>'
            f'<td><a href="{wk["out"]}">{wk["event"]}</a></td>'
            f'<td>Week #{wk["week"]}</td>'
            f'<td>{repo_link}</td>'
            f'<td>{commit_link}</td>'
            f'<td><code>(Jekyll post)</code></td>'
            f'</tr>\n'
        )

        results.append({
            'week': wk['week'], 'date': wk['event'],
            'file': wk['out'],  'commit': short_hash or 'unknown',
        })
        print()

    # Update index.html
    print('Updating index.html ...')
    update_index(new_index_rows)

    # Summary
    print()
    print('=' * 72)
    print(f'Generated {len(results)} pre-website archived pages.')
    print('=' * 72)
    print(f'  {"Week":<7} {"Date":<13} {"Commit":<10} File')
    print('  ' + '-' * 55)
    for r in results:
        print(f'  #{r["week"]:<6} {r["date"]:<13} {r["commit"]:<10} {r["file"]}')
    print()
    print('No git commits were made.')

if __name__ == '__main__':
    main()
