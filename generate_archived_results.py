#!/usr/bin/env python3
"""
Generate standalone archived HTML pages for each VarAC Wednesday weekly results.

Strategy (tag-driven):
  1. Read all  results-YYYYMMDD[*]  tags to discover which weeks exist and which
     commits were explicitly marked as official.
  2. For each week:
       a. The "highest revision" tag (final-rev-2 > final-rev > rev-1 > bare) is
          the initial anchor for that week.
       b. Then scan the lastWeekResults.html commit log for any LATER commits (before
          the next week's first tag commit) that still show the correct event date in
          their <h2>.  These are untagged corrections that should be included.
       c. The LAST such commit (tagged or untagged correction) becomes the official
          archived version for that week.
  3. For early weeks with no tag (7/16, 7/23, 7/30 — before tagging began),
     fall back to h2-date scanning bounded by the first tag (8/6).
  4. Build a fully self-contained HTML page per week (CSS + navbar + footer inlined).
"""

import subprocess, re, os, sys, shutil
from datetime import datetime
from collections import defaultdict

REPO_DIR   = r'C:\Users\admin\OneDrive\Documents\HamRadio\projects\www-varACWednesday'
OUTPUT_DIR = os.path.join(REPO_DIR, 'archived-results')
BRANCH     = 'master'

# ── git helpers ──────────────────────────────────────────────────────────────
def git(*args):
    r = subprocess.run(['git'] + list(args),
                       capture_output=True, text=True, cwd=REPO_DIR,
                       encoding='utf-8', errors='replace')
    return r.stdout.strip()

def show_file(commit_hash, repo_path):
    return git('show', f'{commit_hash}:{repo_path}')

# ── tag helpers ──────────────────────────────────────────────────────────────
TAG_RE = re.compile(r'^results-(\d{8})(.*)?$')   # results-20250806[-rev-1 …]

def tag_priority(suffix):
    """Higher number = higher priority (later revision)."""
    if not suffix:
        return 0
    if suffix.endswith('-final-rev-2'):  return 4
    if suffix.endswith('-final-rev'):    return 3
    if re.search(r'-rev-\d+$', suffix): return 2
    return 1   # unknown suffix

def get_all_results_tags():
    """Return dict: YYYYMMDD -> list of (tag_name, commit_hash, priority)."""
    raw_tags = git('tag', '-l', '--sort=version:refname').splitlines()
    by_date  = defaultdict(list)
    for tag in raw_tags:
        m = TAG_RE.match(tag)
        if not m:
            continue
        date_str = m.group(1)     # YYYYMMDD
        suffix   = m.group(2) or ''
        # resolve lightweight or annotated tag to the final commit hash
        commit   = git('rev-list', '-n', '1', tag)
        prio     = tag_priority(suffix)
        by_date[date_str].append({'tag': tag, 'hash': commit, 'prio': prio, 'suffix': suffix})
    return by_date

# ── file-commit log ──────────────────────────────────────────────────────────
H2_RE = re.compile(
    r'<h2>\s*VarAC Wednesday check-ins\s+'
    r'(\d{1,2}/\d{1,2}/\d{4})'
    r'(?:\s+\(Week\s+#(\d+)\))?'
    r'\s*</h2>',
    re.IGNORECASE
)

def get_file_commits():
    """
    Return list of dicts (oldest→newest) for every commit touching
    docs/lastWeekResults.html on BRANCH.
    """
    raw = git('log', '--format=%H|%ad|%s', '--date=short',
              '--reverse', BRANCH, '--', 'docs/lastWeekResults.html')
    commits = []
    for line in raw.splitlines():
        parts = line.split('|', 2)
        if len(parts) == 3:
            commits.append({'hash': parts[0], 'date': parts[1], 'msg': parts[2]})
    return commits

def annotate_commits(commits):
    """Add h2_date and h2_week to every commit dict (expensive — one git-show each)."""
    print(f"  Fetching file content for {len(commits)} commits …")
    for i, c in enumerate(commits):
        html = show_file(c['hash'], 'docs/lastWeekResults.html')
        m    = H2_RE.search(html)
        c['html']     = html
        c['h2_date']  = m.group(1) if m else None
        c['h2_week']  = m.group(2) if m else None
        if (i + 1) % 10 == 0:
            print(f"    … {i+1}/{len(commits)}")
    return commits

# ── content helpers ──────────────────────────────────────────────────────────
def extract_main(html):
    m = re.search(r'<main>(.*?)</main>', html, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else None

def get_asset(commit_hash, repo_path):
    c = show_file(commit_hash, repo_path)
    if not c.strip():
        c = show_file(BRANCH, repo_path)
    return c

# ── date conversions ─────────────────────────────────────────────────────────
def yyyymmdd_to_mdy(s):
    """20250806 → 8/6/2025"""
    dt = datetime.strptime(s, '%Y%m%d')
    return f"{dt.month}/{dt.day}/{dt.year}"

def mdy_to_yyyymmdd(s):
    """8/6/2025 → 20250806"""
    dt = datetime.strptime(s, '%m/%d/%Y')
    return dt.strftime('%Y%m%d')

def mdy_to_iso(s):
    """8/6/2025 → 2025-08-06"""
    dt = datetime.strptime(s, '%m/%d/%Y')
    return dt.strftime('%Y-%m-%d')

def yyyymmdd_to_iso(s):
    return datetime.strptime(s, '%Y%m%d').strftime('%Y-%m-%d')

# ── commit ordering helper (positional in our sorted list) ───────────────────
def build_hash_index(commits):
    return {c['hash']: i for i, c in enumerate(commits)}

# ── HTML builder ─────────────────────────────────────────────────────────────
LOGO_URL = "https://www.varacwednesday.net/assets/images/VarACWednesdayLogo-White.png"

def build_page(event_date_mdy, week_num, main_content, commit_hash, tag_info):
    css    = get_asset(commit_hash, 'docs/assets/css/varACWed-style.css')
    navbar = get_asset(commit_hash, 'docs/navbar.html')
    footer = get_asset(commit_hash, 'docs/footer.html')

    wk_label = f" (Week #{week_num})" if week_num else ""
    title    = f"VarAC Wednesday Results – {event_date_mdy}{wk_label}"
    tag_note = f"tag: {tag_info}" if tag_info else "no tag (pre-tagging era)"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <!-- Archived from commit {commit_hash[:8]} | {tag_note} -->
  <style>
{css}
  </style>
</head>
<body>

  <header>
    <img src="{LOGO_URL}" alt="VarAC Wednesday" width="300" height="auto" />
    <p>Promoting digital comms excellence for all VarAC enthusiasts</p>
  </header>

  {navbar}

  <main>
{main_content}
  </main>

  {footer}

</body>
</html>"""

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 72)
    print("VarAC Wednesday – Tag-Driven Archived Results Generator")
    print("=" * 72)

    # ── 1. Load tags ──────────────────────────────────────────────────────────
    print("\nReading results tags …")
    tags_by_date = get_all_results_tags()   # YYYYMMDD -> [{tag, hash, prio, suffix}]
    sorted_tag_dates = sorted(tags_by_date.keys())

    print(f"  Found {len(sorted_tag_dates)} tagged week dates: "
          f"{', '.join(sorted_tag_dates)}")

    # For each date pick the highest-priority tag entry
    def best_tag(date):
        return max(tags_by_date[date], key=lambda t: t['prio'])

    # ── 2. Load & annotate file commits ──────────────────────────────────────
    print("\nLoading commits for docs/lastWeekResults.html …")
    all_commits = get_file_commits()
    print(f"  {len(all_commits)} total commits found.")
    all_commits = annotate_commits(all_commits)
    hash_idx    = build_hash_index(all_commits)   # hash -> position (0 = oldest)

    # Position index for tag commits (may not be in the file's own log)
    def commit_position(commit_hash):
        """
        Position in the file-commit list.  If not directly in the list,
        find the closest ancestor that IS in the list via git log --ancestry-path.
        We approximate by scanning for the hash in the full repo log.
        """
        if commit_hash in hash_idx:
            return hash_idx[commit_hash]
        # fall back: get the repo-wide order of this hash vs the file commits
        # by checking if it appears between two known file commits via date
        repo_date = git('show', '-s', '--format=%ad', '--date=short', commit_hash)
        # find the last file commit whose date <= repo_date
        pos = -1
        for i, c in enumerate(all_commits):
            if c['date'] <= repo_date:
                pos = i
        return pos

    # ── 3. Build week list (tagged + untagged early weeks) ───────────────────
    # The "weeks" list will be:  [{'yyyymmdd', 'event_date', 'anchor_hash', 'tag_info'}, …]
    # anchor_hash = highest-priority tag commit for tagged weeks

    weeks = []
    for yyyymmdd in sorted_tag_dates:
        bt = best_tag(yyyymmdd)
        weeks.append({
            'yyyymmdd'   : yyyymmdd,
            'event_date' : yyyymmdd_to_mdy(yyyymmdd),
            'anchor_hash': bt['hash'],
            'tag_info'   : bt['tag'],
        })

    # Also detect early weeks (before tagging started) from the h2 dates
    first_tag_pos = commit_position(weeks[0]['anchor_hash'])
    early_dates   = set()
    for c in all_commits[:first_tag_pos + 1]:
        if c['h2_date']:
            d = mdy_to_yyyymmdd(c['h2_date'])
            if d not in tags_by_date:
                early_dates.add(d)

    for yyyymmdd in sorted(early_dates):
        weeks.insert(0, {
            'yyyymmdd'   : yyyymmdd,
            'event_date' : yyyymmdd_to_mdy(yyyymmdd),
            'anchor_hash': None,     # no tag
            'tag_info'   : None,
        })

    weeks.sort(key=lambda w: w['yyyymmdd'])

    # ── 4. For each week find the OFFICIAL (last corrected) commit ────────────
    print("\n" + "=" * 72)
    print("Determining official commit for each week …")
    print("=" * 72)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []

    for wi, wk in enumerate(weeks):
        date_mdy   = wk['event_date']        # M/D/YYYY
        date_yyyymmdd = wk['yyyymmdd']
        anchor     = wk['anchor_hash']

        # Upper bound: position of NEXT week's LOWEST-priority (= initial) tag commit
        if wi + 1 < len(weeks):
            next_wk     = weeks[wi + 1]
            next_yyyymmdd = next_wk['yyyymmdd']
            if next_yyyymmdd in tags_by_date:
                next_initial_hash = min(tags_by_date[next_yyyymmdd],
                                       key=lambda t: t['prio'])['hash']
                upper_pos = commit_position(next_initial_hash)
            else:
                upper_pos = len(all_commits)   # no upper bound
        else:
            upper_pos = len(all_commits)

        # Anchor position (lower bound): the anchor tag's position (or 0 if none)
        anchor_pos = commit_position(anchor) if anchor else 0

        # Collect all file commits between [anchor_pos, upper_pos) that show
        # the correct event date in the h2
        candidates = [c for c in all_commits[anchor_pos:upper_pos]
                      if c['h2_date'] == date_mdy]

        if not candidates and anchor:
            # anchor commit is not in the file-commit list (it changed a different file)
            # use the file content AT that commit directly
            html    = show_file(anchor, 'docs/lastWeekResults.html')
            m       = H2_RE.search(html)
            h2_date = m.group(1) if m else None
            h2_week = m.group(2) if m else None
            official = {'hash': anchor, 'date': wk['yyyymmdd'],
                        'msg': wk['tag_info'],
                        'html': html, 'h2_date': h2_date, 'h2_week': h2_week}
        elif candidates:
            official = candidates[-1]   # LAST (most corrected) version
        else:
            print(f"  !! SKIP {date_mdy}: no commits found showing this date in h2")
            continue

        # Determine week number
        week_num = official.get('h2_week')

        # Choose filename
        iso = yyyymmdd_to_iso(date_yyyymmdd)
        if week_num:
            filename = f"week-{week_num.zfill(2)}-{iso}.html"
        else:
            filename = f"results-{iso}.html"

        # Build HTML
        main_content = extract_main(official['html'])
        if main_content is None:
            print(f"  !! {date_mdy}: <main> not found in commit {official['hash'][:8]} – skipping")
            continue

        page_html = build_page(date_mdy, week_num, main_content,
                               official['hash'], wk['tag_info'])

        # Report
        tag_display = wk['tag_info'] or '(no tag)'
        print(f"\n  {date_mdy:>12}  Week {'#'+week_num if week_num else 'N/A':5}  "
              f"tag: {tag_display}")
        print(f"    official commit : {official['hash'][:8]}  {official.get('date','')}  "
              f"{official.get('msg','')[:58]}")
        print(f"    anchor commit   : {anchor[:8] if anchor else 'none':8}  "
              f"candidates after anchor: {len(candidates)}")
        print(f"    output file     : {filename}")

        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(page_html)

        results.append({'date': date_mdy, 'yyyymmdd': date_yyyymmdd,
                        'week': week_num, 'file': filename,
                        'commit': official['hash'][:8],
                        'tag': wk['tag_info'] or ''})

    # ── 5. Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print(f"Generated {len(results)} archived result pages -> {OUTPUT_DIR}")
    print("=" * 72)
    print(f"  {'Date':<13} {'Week':<7} {'Commit':<10} {'Tag':<35} File")
    print("  " + "-" * 68)
    for r in results:
        wk = f"#{r['week']}" if r['week'] else 'N/A'
        print(f"  {r['date']:<13} {wk:<7} {r['commit']:<10} "
              f"{r['tag']:<35} {r['file']}")
    print()

    # ── 6. Copy assets (CSS, images) ─────────────────────────────────────────
    assets_src = os.path.join(REPO_DIR, 'docs', 'assets')
    assets_dst = os.path.join(OUTPUT_DIR, 'assets')
    if os.path.isdir(assets_src):
        try:
            # dirs_exist_ok=True overwrites without needing to delete first
            shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
            print(f"Assets copied to {assets_dst}")
        except Exception as e:
            print(f"WARNING: Could not fully copy assets ({e}). "
                  f"Pages will fall back to live-site images.")

    # ── 7. Index page ─────────────────────────────────────────────────────────
    rows = ''
    for r in results:
        wk = f"Week #{r['week']}" if r['week'] else ''
        rows += (f'    <tr><td><a href="{r["file"]}">{r["date"]}</a></td>'
                 f'<td>{wk}</td><td>{r["commit"]}</td>'
                 f'<td><code>{r["tag"]}</code></td></tr>\n')

    index = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>VarAC Wednesday – Archived Results Index</title>
  <style>
    body  {{ font-family: Segoe UI, Arial, sans-serif; padding: 2rem; background:#eef6fc; }}
    h1    {{ color: #014b90; }}
    table {{ border-collapse: collapse; margin-top: 1rem; width: 100%; }}
    th, td {{ border: 1px solid #aac; padding: .45rem .9rem; }}
    th    {{ background: #014b90; color: white; text-align: left; }}
    tr:nth-child(even) {{ background: #d8eaf8; }}
    a     {{ color: #014b90; }}
    code  {{ font-size: .85em; }}
  </style>
</head>
<body>
  <h1>VarAC Wednesday – Archived Weekly Results</h1>
  <p>Each link opens the <em>final corrected</em> version of that week's results page,
     reconstructed from the git history.  The Git Commit column shows the exact
     commit used; the Tag column shows the highest-revision tag for that week.</p>
  <table>
    <tr><th>Event Date</th><th>Week</th><th>Git Commit</th><th>Tag</th></tr>
{rows}  </table>
</body>
</html>"""

    idx_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(idx_path, 'w', encoding='utf-8') as fh:
        fh.write(index)
    print(f"Index page: {idx_path}")
    print("\nDone — no git commits were made.")

if __name__ == '__main__':
    main()
