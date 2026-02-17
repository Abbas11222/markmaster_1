import json
from text_extracr import process_folder
from component_builder import build_weighted_components
from matcher import score_student_answer
from objective_2 import run_objective_2
from question_groupby import group_by_question

MODEL_FOLDER = "model_answer"
STUDENT_FOLDER = "student_answer"
TOTAL_MARKS = 20

model_answer = process_folder(MODEL_FOLDER)
student_answer = process_folder(STUDENT_FOLDER)



# model_components = build_weighted_components(model_answer, TOTAL_MARKS)
# student_components = build_weighted_components(student_answer, TOTAL_MARKS)


# final_score, breakdown = score_student_answer(
#     model_components,
#     student_components,
#     total_marks=TOTAL_MARKS
# )

model_components = build_weighted_components(model_answer, TOTAL_MARKS)
student_components = build_weighted_components(student_answer, TOTAL_MARKS)

model_by_q = group_by_question(model_components)
student_by_q = group_by_question(student_components)

question_scores = {}
question_breakdowns = {}

total_score = 0

for qid in model_by_q.keys():

    q_model = model_by_q.get(qid, [])
    q_student = student_by_q.get(qid, [])

    q_marks = TOTAL_MARKS / len(model_by_q)

    score, breakdown = score_student_answer(
        q_model,
        q_student,
        total_marks=q_marks
    )

    question_scores[qid] = score
    question_breakdowns[qid] = breakdown
    total_score += score

final_score = total_score

print("\n================ FINAL RESULT ================\n")

for qid in question_scores:
    print(f"{qid} SCORE: {round(question_scores[qid],2)}")

print(f"\nTOTAL SCORE: {round(total_score,2)} / {TOTAL_MARKS}\n")

print("Detailed Breakdown:")
print(json.dumps(question_breakdowns, indent=2))


analysis = run_objective_2(
    model_answer=model_answer,
    student_answer=student_answer,
    question_scores=question_scores,
    question_breakdowns=question_breakdowns
)



print("\n===== AI vs HUMAN ANALYSIS =====\n")
for item in analysis:
    print(f"\n######## {item['question']} ########\n")
    print(item["analysis"])

