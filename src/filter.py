"""
Station 2: FILTER
Keeps only jobs that match Siddartha's resume profile:
  - role is SWE / AI / Data / Full-stack (roles_include) and not senior (roles_exclude)
  - experience 0-3 years (drops 5+ year postings)
  - flags jobs that look citizen-only / no-sponsorship
"""


def _has_any(text, needles):
    return any(n in text for n in needles)


def role_ok(title, profile):
    t = title.lower()
    if _has_any(t, profile["roles_exclude"]):
        return False
    return _has_any(t, profile["roles_include"])


def experience_ok(text, profile):
    # drop postings that demand 5+ years
    return not _has_any(text.lower(), profile["exp_exclude_patterns"])


def sponsorship_friendly(text, profile):
    # True if nothing screams "citizen only / no sponsorship"
    return not _has_any(text.lower(), profile["no_sponsor_flags"])


def needs_clearance(text, profile):
    # True if the posting requires a US security clearance -> we DROP these
    return _has_any(text.lower(), profile.get("clearance_exclude", []))


STRONG_US = ["united states", "usa", "u.s.", ", us", "- us", "remote us",
             "remote - us", "us-remote", "remote, us"]


def location_ok(location, profile):
    if not profile.get("us_only"):
        return True
    loc = (location or "").lower()
    if not loc:
        return True  # unknown location -> keep, don't over-filter
    # block-list wins decisively, UNLESS the posting explicitly says US too
    if _has_any(loc, profile.get("us_location_block", [])):
        return _has_any(loc, STRONG_US)
    # not a known foreign location -> keep (US hint, remote, or unclear)
    return True


def filter_jobs(jobs, profile):
    kept = []
    for j in jobs:
        blob = f"{j['title']} {j['description']}"
        if not role_ok(j["title"], profile):
            continue
        if not experience_ok(blob, profile):
            continue
        if needs_clearance(blob, profile):
            continue   # drop security-clearance roles entirely
        if not location_ok(j.get("location", ""), profile):
            continue
        j["opt_friendly"] = sponsorship_friendly(blob, profile)
        kept.append(j)
    return kept
