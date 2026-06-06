"""
Verify Apply links are still live. Removes jobs whose link is confirmed dead
(404/410) so nobody clicks through to a missing posting.

Conservative on purpose: a network blip, timeout, or bot-block (403/405/429)
is treated as ALIVE — we only drop links the server explicitly says are gone.
"""
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (compatible; jobsbuddy-linkcheck/1.0)"


def _alive(url):
    if not url or not url.startswith("http"):
        return True
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status < 400
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return False                 # server says it's gone
        if e.code == 405:                # HEAD not allowed -> try a light GET
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status < 400
            except urllib.error.HTTPError as e2:
                return e2.code not in (404, 410)
            except Exception:
                return True
        return True                      # 403/429/etc -> assume alive
    except Exception:
        return True                      # timeout / DNS blip -> don't drop


def verify_links(jobs, workers=40):
    """Returns the set of job ids (by url) whose link is confirmed dead."""
    targets = [j for j in jobs if j.get("open", True)]
    dead = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for j, ok in zip(targets, ex.map(lambda x: _alive(x.get("url", "")), targets)):
            if not ok:
                dead.append(j)
    return dead
