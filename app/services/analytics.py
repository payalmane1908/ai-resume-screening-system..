from collections import Counter


def skill_distribution(candidates):
    """Return frequency map for matched skills."""
    counter = Counter()
    for c in candidates:
        for s in c.get("matched_skills", []):
            counter[s] += 1
    return dict(counter)


def top_skill_gaps(candidates, limit=8):
    """Return most common missing skills."""
    counter = Counter()
    for c in candidates:
        for s in c.get("missing_skills", []):
            counter[s] += 1
    return dict(counter.most_common(limit))
