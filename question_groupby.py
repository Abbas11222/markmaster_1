from collections import defaultdict

def group_by_question(components):
    grouped = defaultdict(list)
    for c in components:
        grouped[c["question"]].append(c)
    return dict(grouped)
