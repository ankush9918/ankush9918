#!/usr/bin/env python3
"""Generate assets/telemetry.svg (streaks, stats, top languages) in a black + gold theme.

Uses only the standard library and the GitHub GraphQL API.
Run in GitHub Actions with GITHUB_TOKEN. Without a token it writes a placeholder card.
Set DEMO=1 to render with fake numbers (for local visual testing only).
"""
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "ankush9918"
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/telemetry.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}
"""

GOLDS = ["#f9e8b0", "#e6c85a", "#d4af37", "#b8892a", "#8a6a1d"]


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-telemetry",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data or not data.get("data", {}).get("user"):
        raise RuntimeError(f"GraphQL error: {data.get('errors') or 'user not found'}")
    return data["data"]["user"]


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    best = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        best = max(best, run)
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:  # today may still be in progress
        i -= 1
    cur = 0
    while i >= 0 and counts[i] > 0:
        cur += 1
        i -= 1
    return cur, best


def summarize(u):
    repos = u["repositories"]["nodes"]
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    cur, best = streaks(days)
    langs = {}
    for repo in repos:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]
    top = [(n, s * 100.0 / total) for n, s in top]
    tiles = [
        ("CONTRIBUTIONS", cal["totalContributions"]),
        ("CURRENT STREAK", cur),
        ("BEST STREAK", best),
        ("STARS EARNED", sum(r["stargazerCount"] for r in repos)),
        ("PULL REQUESTS", cc["totalPullRequestContributions"]),
        ("FOLLOWERS", u["followers"]["totalCount"]),
    ]
    return tiles, top


def demo():
    tiles = [("CONTRIBUTIONS", 312), ("CURRENT STREAK", 4), ("BEST STREAK", 21),
             ("STARS EARNED", 12), ("PULL REQUESTS", 9), ("FOLLOWERS", 27)]
    top = [("JavaScript", 41.0), ("Python", 27.5), ("HTML", 18.0), ("CSS", 9.5), ("TypeScript", 4.0)]
    return tiles, top


def placeholder():
    names = ["CONTRIBUTIONS", "CURRENT STREAK", "BEST STREAK", "STARS EARNED", "PULL REQUESTS", "FOLLOWERS"]
    return [(n, "--") for n in names], []


def render(tiles, top):
    W, H = 1200, 450
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub telemetry">')
    a('''<defs>
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f9e8b0"/><stop offset="0.5" stop-color="#d4af37"/><stop offset="1" stop-color="#a67c1a"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d4af37" stop-opacity="0.9"/><stop offset="1" stop-color="#d4af37" stop-opacity="0"/></linearGradient>
<radialGradient id="glow" cx="0.5" cy="0" r="0.9"><stop offset="0" stop-color="#d4af37" stop-opacity="0.12"/><stop offset="1" stop-color="#d4af37" stop-opacity="0"/></radialGradient>
<clipPath id="barclip"><rect x="50" y="318" width="1100" height="16" rx="8"/></clipPath>
<style>
.sans{font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif}
.serif{font-family:Georgia,'Times New Roman',serif}
.cap{font-size:24px;letter-spacing:9px;fill:#d4af37}
.lab{font-size:14px;letter-spacing:1px;fill:#a29c86}
.val{font-size:54px;font-weight:700;fill:url(#gold)}
.nm{font-size:21px;fill:#f4efe4}
.pc{font-size:19px;fill:#a29c86}
</style></defs>''')
    a(f'<rect width="{W}" height="{H}" rx="22" fill="#05060a"/>')
    a(f'<rect width="{W}" height="{H}" rx="22" fill="url(#glow)"/>')
    a(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="none" stroke="url(#gold)" stroke-opacity="0.5" stroke-width="2"/>')

    a('<text x="60" y="70" class="sans cap">GITHUB TELEMETRY</text>')
    a('<rect x="480" y="61" width="660" height="2" fill="url(#fade)"/>')

    for i, (label, val) in enumerate(tiles):
        x = 50 + i * 186
        a(f'<g transform="translate({x} 100)">')
        a('<rect width="170" height="140" rx="16" fill="#0b0d14" stroke="#d4af37" stroke-opacity="0.35"/>')
        a('<rect x="16" y="1" width="138" height="3" rx="1.5" fill="url(#gold)" opacity="0.9"/>')
        a(f'<text x="85" y="82" text-anchor="middle" class="serif val">{escape(str(val))}</text>')
        a(f'<text x="85" y="116" text-anchor="middle" class="sans lab">{escape(label)}</text>')
        a('</g>')

    a('<text x="60" y="288" class="sans" style="font-size:20px;letter-spacing:7px;fill:#d4af37">TOP LANGUAGES</text>')
    a('<rect x="50" y="318" width="1100" height="16" rx="8" fill="#14161f"/>')
    if top:
        tot = sum(p for _, p in top) or 1
        a('<g clip-path="url(#barclip)">')
        x = 50.0
        for i, (name, pct) in enumerate(top):
            w = 1100.0 * pct / tot
            a(f'<rect x="{x:.1f}" y="318" width="0" height="16" fill="{GOLDS[i]}">'
              f'<animate attributeName="width" from="0" to="{max(w-3,1):.1f}" dur="1.1s" begin="{i*0.18:.2f}s" fill="freeze"/></rect>')
            x += w
        a('</g>')
        for i, (name, pct) in enumerate(top):
            lx = 50 + i * 220
            a(f'<circle cx="{lx+8}" cy="372" r="7" fill="{GOLDS[i]}"/>')
            a(f'<text x="{lx+26}" y="379" class="sans nm">{escape(name)}</text>')
            a(f'<text x="{lx+26}" y="406" class="sans pc">{pct:.1f}%</text>')
    else:
        a('<text x="50" y="378" class="sans nm">Waiting for first update...</text>')
        a('<text x="50" y="408" class="sans pc">Actions tab, Update Profile Stats, Run workflow</text>')

    a(f'<text x="1150" y="432" text-anchor="end" class="sans" style="font-size:14px;letter-spacing:3px;fill:#6f6a58">LAST 12 MONTHS  ·  AUTO-UPDATED</text>')
    a('</svg>')
    return "\n".join(o)


def main():
    if os.environ.get("DEMO") == "1":
        tiles, top = demo()
    elif not TOKEN:
        tiles, top = placeholder()
    else:
        tiles, top = summarize(fetch())
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(tiles, top))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
