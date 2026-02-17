from sklearn.metrics.pairwise import cosine_similarity
from embedder import embed


def score_student_answer(
    model_components,
    student_components,
    total_marks,
    threshold=0.10,
    max_penalty=2.0
):

    # If no model → nothing to score
    if not model_components:
        return 0.0, []

    breakdown = []
    total_score = 0.0

    # ================================
    # CASE 1 — NO STUDENT ANSWER
    # ================================
    if not student_components:
        for m in model_components:
            breakdown.append({
                "component": m["id"],
                "topic": m["topic"],
                "weight": float(round(m["weight"], 2)),
                "similarity": 0.0,
                "score": 0.0
            })

        breakdown.append({
            "penalty_reason": "No student answer / unrelated content",
            "penalty": 0.0
        })

        return 0.0, breakdown

    # ================================
    # NORMAL MATCHING
    # ================================

    model_texts = [c["text"] for c in model_components]
    student_texts = [c["text"] for c in student_components]

    model_embs = embed(model_texts)
    student_embs = embed(student_texts)

    used_students = set()
    matched_student_weight = 0.0

    for i, m in enumerate(model_components):
        sims = cosine_similarity([model_embs[i]], student_embs)[0]

        best_j = -1
        best_sim = 0.0

        for j, sim in enumerate(sims):
            if j not in used_students and sim > best_sim:
                best_sim = float(sim)
                best_j = j

        earned = 0.0
        if best_sim >= threshold and best_j != -1:
            earned = float(best_sim * m["weight"])
            used_students.add(best_j)
            matched_student_weight += student_components[best_j]["weight"]

        total_score += earned

        breakdown.append({
            "component": m["id"],
            "topic": m["topic"],
            "weight": float(round(m["weight"], 2)),
            "similarity": float(round(best_sim, 2)),
            "score": float(round(earned, 2))
        })

    total_student_weight = sum(c["weight"] for c in student_components)
    unmatched_weight = total_student_weight - matched_student_weight

    penalty = 0.0
    if total_student_weight > 0:
        penalty = float((unmatched_weight / total_student_weight) * max_penalty)

    final_score = max(0.0, min(float(total_marks), float(total_score - penalty)))

    breakdown.append({
        "penalty_reason": "Irrelevant or extra content",
        "penalty": float(round(penalty, 2))
    })

    return float(round(final_score, 2)), breakdown