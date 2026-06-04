"""
Station 1: SCRAPE
Pulls open jobs from company ATS feeds (Greenhouse, Lever, Ashby).
Uses only the Python standard library -- no pip installs needed.
Every adapter returns a list of normalized dicts:
  { company, title, location, url, description, posted_at, source }
"""
import json
import urllib.request
import urllib.error

UA = "opt-friendly-jobs/1.0 (+https://github.com/SIDDARTHAREDDY8)"
TIMEOUT = 20


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ---------- Greenhouse ----------
def scrape_greenhouse(slug, company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    data = _get_json(url)
    out = []
    for j in data.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        out.append({
            "company": company,
            "title": j.get("title", ""),
            "location": loc,
            "url": j.get("absolute_url", ""),
            "description": _strip_html(j.get("content", "")),
            "posted_at": j.get("updated_at", "") or j.get("first_published", ""),
            "source": "greenhouse",
        })
    return out


# ---------- Lever ----------
def scrape_lever(slug, company):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    data = _get_json(url)
    out = []
    for j in data:
        cats = j.get("categories", {}) or {}
        out.append({
            "company": company,
            "title": j.get("text", ""),
            "location": cats.get("location", ""),
            "url": j.get("hostedUrl", ""),
            "description": _strip_html(j.get("descriptionPlain", "") or j.get("description", "")),
            "posted_at": "",
            "source": "lever",
        })
    return out


# ---------- Ashby ----------
def scrape_ashby(slug, company):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false"
    data = _get_json(url)
    out = []
    for j in data.get("jobs", []):
        out.append({
            "company": company,
            "title": j.get("title", ""),
            "location": j.get("location", "") or j.get("locationName", ""),
            "url": j.get("jobUrl", "") or j.get("applyUrl", ""),
            "description": _strip_html(j.get("descriptionPlain", "") or j.get("description", "")),
            "posted_at": j.get("publishedAt", ""),
            "source": "ashby",
        })
    return out


# ---------- Workday ----------
def scrape_workday(slug, company):
    # slug format: "tenant|dc|site"  e.g. "nvidia|wd5|NVIDIAExternalCareerSite"
    tenant, dc, site = slug.split("|")
    base = f"https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    out, offset = [], 0
    for _ in range(5):  # up to 5 pages (100 jobs) per company
        body = json.dumps({"limit": 20, "offset": offset, "searchText": ""}).encode()
        req = urllib.request.Request(base, data=body,
                                     headers={"User-Agent": UA, "Content-Type": "application/json",
                                              "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        postings = data.get("jobPostings", [])
        if not postings:
            break
        host = f"https://{tenant}.{dc}.myworkdayjobs.com/en-US/{site}"
        for j in postings:
            path = j.get("externalPath", "")
            out.append({
                "company": company,
                "title": j.get("title", ""),
                "location": j.get("locationsText", ""),
                "url": host + path,
                "description": j.get("title", ""),  # Workday list view has no full text
                "posted_at": j.get("postedOn", ""),
                "source": "workday",
            })
        offset += 20
        if offset >= data.get("total", 0):
            break
    return out


def _strip_html(s):
    if not s:
        return ""
    import re
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
           .replace("&#39;", "'").replace("&quot;", '"').replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", s).strip()


ADAPTERS = {
    "greenhouse": scrape_greenhouse,
    "lever": scrape_lever,
    "ashby": scrape_ashby,
    "workday": scrape_workday,
}


def scrape_all(companies):
    jobs = []
    for c in companies:
        fn = ADAPTERS.get(c["ats"])
        if not fn:
            continue
        try:
            got = fn(c["slug"], c["company"])
            jobs.extend(got)
            print(f"  [ok]   {c['company']:<14} ({c['ats']}) -> {len(got)} jobs")
        except urllib.error.HTTPError as e:
            print(f"  [skip] {c['company']:<14} ({c['ats']}) HTTP {e.code}")
        except Exception as e:
            print(f"  [skip] {c['company']:<14} ({c['ats']}) {type(e).__name__}")
    return jobs
