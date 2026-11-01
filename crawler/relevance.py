
import re


IT_KEYWORDS = [
    "it support",
    "information technology",
    "teknologi informasi",
    "teknik informatika",
    "sistem informasi",
    "sistem komputer",
    "computer science",
    "software engineer",
    "software developer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "web developer",
    "mobile developer",
    "android developer",
    "flutter developer",
    "devops",
    "cloud engineer",
    "network engineer",
    "system administrator",
    "data engineer",
    "ai engineer",
    "artificial intelligence",
    "machine learning",
    "cyber security",
    "database administrator",
    "programmer",
    "developer",
]


def normalize(value):
    value = value or ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def classify_relevance(job):
    searchable_text = normalize(" ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("majors_raw", ""),
        job.get("location", ""),
    ]))

    matched_keywords = [
        keyword
        for keyword in IT_KEYWORDS
        if normalize(keyword) in searchable_text
    ]

    return {
        "is_relevant": bool(matched_keywords),
        "matched_keywords": matched_keywords,
    }
