import json
from objective2_llm import compare_ai_with_human


def flatten_text(extracted):
    texts = []

    def recurse_topic(node, prefix=""):
        topic = node.get("topic", "")
        content = node.get("content", "")

        if topic or content:
            texts.append(f"{prefix}{topic}. {content}".strip())

        for sub in node.get("sub_topics", []):
            recurse_topic(sub, prefix)

    for paper in extracted:
        for q in paper.get("questions", []):
            qid = q.get("question_id", "")
            qtitle = q.get("question_title", "")

            for part in q.get("parts", []):
                part_id = part.get("part_id", "")
                prefix = f"{qid} ({part_id}) - "

                recurse_topic(part, prefix)

    return "\n".join(texts)




def run_objective_2(
    model_answer,
    student_answer,
    question_scores,
    question_breakdowns
):

    model_text = flatten_text(model_answer)
    student_text = flatten_text(student_answer)

    full_analysis = []

    for qid in question_scores:

        print(f"\n===== HUMAN INPUT FOR {qid} =====")

        human_score = float(input(f"Enter human score for {qid}: "))

        human_feedback = {}
        print("Enter feedback per topic:")

        for item in question_breakdowns[qid]:
            if "topic" in item:
                fb = input(f"{item['topic']}: ").strip()
                if fb:
                    human_feedback[item["topic"]] = fb

        analysis = compare_ai_with_human(
            model_text=model_text,
            student_text=student_text,
            ai_score=question_scores[qid],
            ai_breakdown=question_breakdowns[qid],
            human_score=human_score,
            human_feedback=human_feedback
        )

        full_analysis.append({
            "question": qid,
            "analysis": analysis
        })

    return full_analysis