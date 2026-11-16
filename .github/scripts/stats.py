#!/usr/bin/env python3
"""Generate assets/telemetry.svg (stats + top languages) in a dark neon theme.

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
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""

FALLBACK_COLORS = ["#00f5d4", "#7b61ff", "#ff2e97", "#ffd166", "#59b4ff"]


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


def summarize(u):
    repos = u["repositories"]["nodes"]
    cc = u["contributionsCollection"]
    langs = {}
    for repo in repos:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            cur = langs.setdefault(name, {"size": 0, "color": e["node"]["color"]})
            cur["size"] += e["size"]
    total = sum(v["size"] for v in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: kv[1]["size"], reverse=True)[:5]
    top = [
        (n, v["size"] * 100.0 / total, v["color"] or FALLBACK_COLORS[i % 5])
        for i, (n, v) in enumerate(top)
    ]
    stats = [
        ("STARS EARNED", sum(r["stargazerCount"] for r in repos)),
        ("COMMITS (1Y)", cc["totalCommitContributions"]),
        ("PULL REQUESTS", cc["totalPullRequestContributions"]),
        ("ISSUES", cc["totalIssueContributions"]),
        ("PUBLIC REPOS", u["repositories"]["totalCount"]),
        ("FOLLOWERS", u["followers"]["totalCount"]),
    ]
    return stats, top, cc["contributionCalendar"]["totalContributions"]


def demo():
    stats = [("STARS EARNED", 12), ("COMMITS (1Y)", 214), ("PULL REQUESTS", 9),
             ("ISSUES", 4), ("PUBLIC REPOS", 18), ("FOLLOWERS", 27)]
    top = [("JavaScript", 41.0, "#f1e05a"), ("Python", 27.5, "#3572A5"), ("HTML", 18.0, "#e34c26"),
           ("CSS", 9.5, "#563d7c"), ("TypeScript", 4.0, "#3178c6")]
    return stats, top, 312


def placeholder():
    names = ["STARS EARNED", "COMMITS (1Y)", "PULL REQUESTS", "ISSUES", "PUBLIC REPOS", "FOLLOWERS"]
    return [(n, "--") for n in names], [], None


def render(stats, top, total):
    W, H = 1200, 320
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub telemetry">')
    a('''<defs>
<linearGradient id="neon" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f5d4"/><stop offset="0.5" stop-color="#7b61ff"/><stop offset="1" stop-color="#ff2e97"/></linearGradient>
<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.m{font-family:'JetBrains Mono','Fira Code','Courier New',monospace}
.lab{font-size:13px;letter-spacing:2px;fill:#6b7bb8}
.val{font-size:34px;font-weight:700;fill:#ffffff}
.ttl{font-size:16px;letter-spacing:5px;fill:#00f5d4}
.ln{font-size:16px;fill:#e6ecff}
.pc{font-size:15px;fill:#8fa0ff}
</style></defs>''')
    a(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="#070b1c" stroke="url(#neon)" stroke-width="2"/>')
    a('<line x1="600" y1="30" x2="600" y2="290" stroke="#7b61ff" stroke-opacity="0.35" stroke-dasharray="4 8"/>')

    # left: stats
    a('<text x="44" y="52" class="m ttl">// STATS</text>')
    for i, (label, val) in enumerate(stats):
        col, row = i % 2, i // 2
        x = 44 + col * 270
        y = 100 + row * 74
        a(f'<text x="{x}" y="{y}" class="m val" filter="url(#glow)">{escape(str(val))}</text>')
        a(f'<text x="{x}" y="{y+24}" class="m lab">{escape(label)}</text>')

    # right: languages
    a('<text x="644" y="52" class="m ttl">// TOP LANGUAGES</text>')
    if top:
        for i, (name, pct, color) in enumerate(top):
            y = 92 + i * 44
            bw = 300 * pct / max(top[0][1], 1)
            a(f'<text x="644" y="{y}" class="m ln">{escape(name)}</text>')
            a(f'<text x="1156" y="{y}" class="m pc" text-anchor="end">{pct:.1f}%</text>')
            a(f'<rect x="644" y="{y+10}" width="512" height="8" rx="4" fill="#101736"/>')
            bar_w = 512 * pct / 100.0
            a(f'<rect x="644" y="{y+10}" width="0" height="8" rx="4" fill="{escape(color)}" filter="url(#glow)">'
              f'<animate attributeName="width" from="0" to="{bar_w:.1f}" dur="1.2s" begin="{i*0.15:.2f}s" fill="freeze"/></rect>')
    else:
        a('<text x="644" y="120" class="m ln">Waiting for first update...</text>')
        a('<text x="644" y="150" class="m pc">Actions tab -&gt; Update Profile Stats -&gt; Run workflow</text>')

    if total is not None:
        a(f'<text x="1156" y="304" class="m lab" text-anchor="end">{total} CONTRIBUTIONS IN THE LAST YEAR</text>')
    a('</svg>')
    return "\n".join(o)


def main():
    if os.environ.get("DEMO") == "1":
        stats, top, total = demo()
    elif not TOKEN:
        stats, top, total = placeholder()
    else:
        stats, top, total = summarize(fetch())
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(stats, top, total))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
