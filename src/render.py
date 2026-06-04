"""
Station 5: WRITE PAGE  (accumulating archive)
Lists EVERY job ever found, grouped by the date it was added.
Newest day on top, older days below. Within a day: sponsors + best match first.
"""
from datetime import datetime, timezone

BADGE = {"high": "✅ Sponsors (High)", "medium": "✅ Sponsors (Med)", "low": "✅ Sponsors (Low)"}


def _visa_cell(job):
    if job.get("sponsors_visa"):
        return BADGE.get(job.get("sponsor_tier"), "✅ Sponsors")
    if not job.get("opt_friendly", True):
        return "⚠️ May not sponsor"
    return "— unknown"


def _within_day_sort(j):
    tier_rank = {"high": 3, "medium": 2, "low": 1}.get(j.get("sponsor_tier"), 0)
    return (j.get("sponsors_visa", False), tier_rank, j.get("match_score", 0))


def render_readme(jobs, profile, today):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(jobs)
    open_now = sum(1 for j in jobs if j.get("open", True))
    new_today = sum(1 for j in jobs if j.get("first_seen") == today)

    # group by the date a job was first added
    by_day = {}
    for j in jobs:
        by_day.setdefault(j.get("first_seen", "unknown"), []).append(j)
    days = sorted(by_day.keys(), reverse=True)   # newest day first

    L = []
    L.append("# 🌍 OPT-Friendly Software / AI / Data Jobs")
    L.append("")
    L.append(f"> {profile.get('tagline', '')}")
    L.append("")
    L.append("Auto-updated job board for **international students on OPT** — "
             "**Software / AI / Data Engineering** roles at companies with a "
             "**known H1B sponsorship history**. New jobs are added to the top every day.")
    L.append("")
    L.append(f"**Last updated:** {now}  •  **Total jobs:** {total}  "
             f"•  **Open now:** {open_now}  •  **🆕 Added today:** {new_today}")
    L.append("")
    L.append("**Legend:** ✅ Sponsors = recent H1B filing history • 🆕 = added today • "
             "🔒 = no longer listed (kept for history) • Match % = fit vs. this profile. "
             "No security-clearance or non-US roles.")
    L.append("")

    for day in days:
        group = sorted(by_day[day], key=_within_day_sort, reverse=True)
        nice = _pretty_date(day)
        L.append(f"## 🗓️ {nice} — {len(group)} jobs")
        L.append("")
        L.append("| | Company | Role | Location | Visa | Match | Status | Apply |")
        L.append("|--|--|--|--|--|--|--|--|")
        for j in group:
            flag = "🆕" if j.get("first_seen") == today else ""
            title = (j.get("title", "")).replace("|", "/")
            loc = (j.get("location") or "—").replace("|", "/")[:28]
            status = "Open" if j.get("open", True) else "🔒 Closed"
            L.append(f"| {flag} | {j.get('company','')} | {title} | {loc} | "
                     f"{_visa_cell(j)} | **{j.get('match_score', 0)}%** | {status} | "
                     f"[Apply]({j.get('url','')}) |")
        L.append("")

    L.append("<sub>Built with a free Python scraper + GitHub Actions — no paid APIs. "
             "Sponsorship tiers are indicative; verify on the posting. "
             "Closed roles are kept for history. Data from public ATS feeds "
             "(Greenhouse, Lever, Ashby, Workday).</sub>")
    L.append("")
    return "\n".join(L)


def _pretty_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        return d
