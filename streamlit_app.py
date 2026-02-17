import streamlit as st
import json
import os

from text_extracr import process_folder
from component_builder import build_weighted_components
from matcher import score_student_answer
from objective_2 import flatten_text
from objective2_llm import compare_ai_with_human
from question_groupby import group_by_question

# NEW
from upload_pics import prepare_upload_folder, clear_temp_folder


# ---------------- CONFIG ----------------
DEFAULT_MODEL_FOLDER = "model_answer"
DEFAULT_STUDENT_FOLDER = "student_answer"

st.set_page_config(page_title="MarkMaster", layout="wide")
st.title("📘 MarkMaster – AI Assisted Grading")


# ---------------- SESSION STATE ----------------
for key in [
    "processed",
    "analysis_done",
    "question_scores",
    "question_breakdowns",
    "model_answer",
    "student_answer",
    "analysis_results",
    "temp_model_folder",
    "temp_student_folder"
]:
    if key not in st.session_state:
        st.session_state[key] = None


# =====================================================
# OBJECTIVE 1 — INPUT SOURCE
# =====================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("Model Answer Images")
    model_uploads = st.file_uploader(
        "Upload model answer pages",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

with col2:
    st.subheader("Student Answer Images")
    student_uploads = st.file_uploader(
        "Upload student answer pages",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )


# =====================================================
# OBJECTIVE 1 — AI GRADING
# =====================================================

st.header("AI Grading")

TOTAL_MARKS = st.number_input(
    "Enter total exam marks",
    min_value=1.0,
    step=5.0,
    value=10.0
)


from upload_pics import (
    prepare_upload_folder,
    clear_temp_folder,
    folder_has_images
)

# =====================================================
# PROCESS BUTTON
# =====================================================

if st.button("🚀 Start Processing", use_container_width=True):

    with st.spinner("Preparing files..."):

        # ---------- MODEL SOURCE ----------
        if model_uploads:
            model_folder = prepare_upload_folder(model_uploads, "model_")
            st.session_state.temp_model_folder = model_folder
        else:
            model_folder = DEFAULT_MODEL_FOLDER

        # ---------- STUDENT SOURCE ----------
        if student_uploads:
            student_folder = prepare_upload_folder(student_uploads, "student_")
            st.session_state.temp_student_folder = student_folder
        else:
            student_folder = DEFAULT_STUDENT_FOLDER

    # =====================================================
    # ✅ VALIDATION LOGIC (NEW)
    # =====================================================

    model_exists = folder_has_images(model_folder)
    student_exists = folder_has_images(student_folder)

    if not model_exists and not student_exists:
        st.error("❌ No model or student answer images found.")
        st.info("Upload images OR place them in default folders.")
        st.stop()

    if not model_exists:
        st.error("❌ Model answer images not found.")
        st.info("Upload model answer pages or check model_answer folder.")
        st.stop()

    if not student_exists:
        st.error("❌ Student answer images not found.")
        st.info("Upload student answer pages or check student_answer folder.")
        st.stop()

    # =====================================================
    # SAFE TO PROCESS
    # =====================================================

    with st.spinner("Processing and grading..."):

        model_answer = process_folder(model_folder)
        student_answer = process_folder(student_folder)

        model_components = build_weighted_components(model_answer, TOTAL_MARKS)
        student_components = build_weighted_components(student_answer, TOTAL_MARKS)

        model_by_q = group_by_question(model_components)
        student_by_q = group_by_question(student_components)

        question_scores = {}
        question_breakdowns = {}

        total_score = 0
        per_question_marks = TOTAL_MARKS / len(model_by_q)

        for qid in model_by_q:

            score, breakdown = score_student_answer(
                model_by_q[qid],
                student_by_q.get(qid, []),
                total_marks=per_question_marks
            )

            question_scores[qid] = score
            question_breakdowns[qid] = breakdown
            total_score += score

        st.session_state.model_answer = model_answer
        st.session_state.student_answer = student_answer
        st.session_state.question_scores = question_scores
        st.session_state.question_breakdowns = question_breakdowns
        st.session_state.total_score = total_score
        st.session_state.processed = True
        st.session_state.analysis_results = {}

        clear_temp_folder(st.session_state.temp_model_folder)
        clear_temp_folder(st.session_state.temp_student_folder)



# =====================================================
# SHOW AI RESULTS
# =====================================================

if st.session_state.processed:

    st.success(
        f"✅ TOTAL AI SCORE: {round(st.session_state.total_score,2)} / {TOTAL_MARKS}"
    )

    st.subheader("📊 Question-wise Scores")

    for qid, score in st.session_state.question_scores.items():
        st.write(f"{qid} → {round(score,2)} marks")

    st.divider()
    st.subheader("📑 Question Breakdown")

    for qid in st.session_state.question_breakdowns:
        if st.button(f"Show Breakdown — {qid}", key=f"break_{qid}"):
            st.json(st.session_state.question_breakdowns[qid])


# =====================================================
# OBJECTIVE 2 — HUMAN MODERATION
# =====================================================

if st.session_state.processed:

    st.divider()
    st.header("Objective 2: Human vs AI Moderation")

    model_text = flatten_text(st.session_state.model_answer)
    student_text = flatten_text(st.session_state.student_answer)

    for qid in st.session_state.question_scores:

        ai_score_q = st.session_state.question_scores[qid]
        breakdown_q = st.session_state.question_breakdowns[qid]

        with st.expander(f"Moderation Panel — {qid}"):

            st.write(f"AI Score: {round(ai_score_q,2)}")

            human_score = st.number_input(
                f"Human score for Question {qid}",
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                key=f"human_score_{qid}"
            )

            st.write("Topic Feedback")
            human_feedback = {}

            for item in breakdown_q:
                if "topic" in item:
                    fb = st.text_area(
                        f"{item['topic']}",
                        key=f"feedback_{qid}_{item['topic']}"
                    )
                    if fb.strip():
                        human_feedback[item["topic"]] = fb.strip()

            if st.button(f"Run Analysis — {qid}", key=f"analyze_{qid}"):

                with st.spinner(f"Analyzing {qid}..."):

                    analysis = compare_ai_with_human(
                        model_text=model_text,
                        student_text=student_text,
                        ai_score=ai_score_q,
                        ai_breakdown=breakdown_q,
                        human_score=human_score,
                        human_feedback=human_feedback if human_feedback else None
                    )

                    st.session_state.analysis_results[qid] = analysis
                    st.success("Analysis complete")

            if qid in st.session_state.analysis_results:
                st.markdown("### Analysis Result")
                st.markdown(st.session_state.analysis_results[qid])