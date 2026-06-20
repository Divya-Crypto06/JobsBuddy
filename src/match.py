"""

Station 4a: MATCH SCORE

Scores each job 0-100 against the resume skills (rules-based, no AI).

Score = how many of MY skills the job mentions + small role/sponsor boosts.

 

Tuned for Divya's resume: Senior Full Stack Developer (Java/Spring Boot,

React/TypeScript, Node.js, AWS+Azure, Kubernetes), banking/fintech/SaaS

background. Skill list and role_boost keywords below come directly from

that resume -- not a generic SWE template -- so keep them in sync if the

resume changes (see sync_skills.py).

"""

import re

 

 

def _skill_pattern(skill):

    # Word-boundary match so short tokens (e.g. "css", "jpa", "iam", "rds",

    # "s3") don't false-positive as substrings inside unrelated words.

    # \b doesn't work well around tokens with non-word characters

    # (pl/sql), so escape the skill and only require a boundary where the

    # edge character is actually a word character.

    esc = re.escape(skill)

    left = r"\b" if skill[0].isalnum() else ""

    right = r"\b" if skill[-1].isalnum() else ""

    return re.compile(left + esc + right, re.IGNORECASE)

 

 

# Role keywords reflect Divya's actual target roles (full stack / Java /

# backend / banking-fintech engineer), not a generic "ai/data/software"

# list. Matched with word boundaries against the job title only.

_ROLE_BOOST_PATTERNS = [_skill_pattern(r) for r in [

    "full stack", "fullstack", "full-stack",

    "java",

    "backend",

    "software engineer",

    "software developer",

    "platform engineer",

]]

 

 

def score_job(job, profile):

    blob = f"{job['title']} {job['description']}".lower()

    skills = profile["skills"]

    hit = [s for s in skills if _skill_pattern(s).search(blob)]

    # de-dupe near-identical skill tokens for the display list

    seen, matched = set(), []

    for s in hit:

        key = s.replace(".", "").replace("-", "").replace("/", "")

        if key not in seen:

            seen.add(key)

            matched.append(s)

    # base: proportion of a "good match" (cap at ~10 skills = strong)

    base = min(len(matched), 10) / 10 * 80      # up to 80 pts from skills

    title_lower = job["title"].lower()

    role_boost = 12 if any(p.search(title_lower) for p in _ROLE_BOOST_PATTERNS) else 0

    sponsor_boost = 8 if job.get("sponsors_visa") else 0

    score = int(min(100, base + role_boost + sponsor_boost))

    job["match_score"] = score

    job["matched_skills"] = matched[:6]

    return job

 

 

def score_all(jobs, profile):

    return [score_job(j, profile) for j in jobs]
