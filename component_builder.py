def collect_full_text(topic):
    """
    Recursively collect text from topic and all descendants.
    Returns a single combined string.
    """
    texts = []

    def recurse(node):
        topic_name = node.get("topic", "")
        content = node.get("content", "")
        texts.append(f"{topic_name}. {content}".strip())

        for sub in node.get("sub_topics", []):
            recurse(sub)

    recurse(topic)
    return " ".join(texts)



def flatten_topic(topic, parent_id, weight, components, question_id, part_id,
                  main_ratio=0.3):

    subs = topic.get("sub_topics", [])

    # FULL hierarchical text
    full_text = collect_full_text(topic)

    # ==============================
    # CASE 1 — NO SUBTOPICS
    # ==============================
    if not subs:
        components.append({
            "id": parent_id,
            "question": question_id,
            "part": part_id,
            "topic": topic.get("topic", ""),
            "text": full_text,
            "weight": float(weight)
        })
        return

    # ==============================
    # CASE 2 — HAS SUBTOPICS
    # ==============================

    main_weight = weight * main_ratio
    remaining_weight = weight * (1 - main_ratio)
    sub_weight = remaining_weight / len(subs)

    # Parent contains ALL descendant info
    components.append({
        "id": parent_id,
        "question": question_id,
        "part": part_id,
        "topic": topic.get("topic", ""),
        "text": full_text,
        "weight": float(main_weight)
    })

    # Recurse normally
    for i, s in enumerate(subs, 1):
        flatten_topic(
            s,
            f"{parent_id}.S{i}",
            sub_weight,
            components,
            question_id,
            part_id,
            main_ratio
        )




def build_weighted_components(extracted_papers, total_marks):
    """
    extracted_papers = list of files
    each file contains multiple questions
    """

    components = []
    all_questions = []

    for paper in extracted_papers:
        all_questions.extend(paper.get("questions", []))

    if not all_questions:
        return []

    question_weight = total_marks / len(all_questions)

    for q_index, q in enumerate(all_questions, 1):
        qid = q.get("question_id", f"Q{q_index}")
        parts = q.get("parts", [])

        if not parts:
            continue

        part_weight = question_weight / len(parts)

        for p_index, part in enumerate(parts, 1):
            part_id = part.get("part_id", f"P{p_index}")

            flatten_topic(
                part,
                f"{qid}.P{p_index}",
                part_weight,
                components,
                qid,
                part_id
            )

    return components
