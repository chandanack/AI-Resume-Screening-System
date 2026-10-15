from flask import Flask, render_template, request, session, send_file
import os

from preprocessing.preprocess import (
    extract_text_from_pdf,
    extract_text_from_docx,
    clean_text
)

from preprocessing.skill_extractor import (
    extract_skills,
    extract_education,
    extract_certifications,
    extract_experience,
    extract_keywords
)

from database.db import get_connection
from models.similarity_model import calculate_similarity
from models.ranking_model import rank_candidates

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from xml.sax.saxutils import escape


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = "ai_resume_screening_secret_2026"


# ============================================================
# UPLOAD FOLDER
# ============================================================

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# AI IMPROVEMENT RECOMMENDATION
# ============================================================

def generate_improvement_recommendation(
    matched_skills,
    missing_skills,
    match_percentage,
    similarity_score,
    final_score
):
    """
    Generates an explainable recommendation using
    the screening results already calculated by the system.
    """

    if missing_skills:

        missing_text = ", ".join(
            str(skill).title()
            for skill in missing_skills[:5]
        )

        if final_score >= 80:

            return (
                f"The candidate has a strong overall profile with "
                f"{match_percentage:.1f}% skill matching and "
                f"{similarity_score:.1f}% resume-to-job similarity. "
                f"The main improvement area is: {missing_text}. "
                f"Developing these skills could make the profile "
                f"even stronger for this role."
            )

        elif final_score >= 60:

            return (
                f"The candidate shows a moderate-to-strong fit for "
                f"the role. The resume matches {match_percentage:.1f}% "
                f"of the detected job skills. Recommended focus areas "
                f"include: {missing_text}. Improving these skills "
                f"could increase suitability for the position."
            )

        else:

            return (
                f"The candidate currently has a lower suitability "
                f"score of {final_score:.1f}%. The main detected "
                f"skill gaps are: {missing_text}. Building these "
                f"skills and strengthening relevant project or "
                f"experience evidence could improve the profile."
            )

    else:

        if final_score >= 80:

            return (
                "The candidate demonstrates a strong match with "
                "the detected job requirements. All detected "
                "technical skills are present in the resume. "
                "The candidate can be prioritized for further "
                "recruitment evaluation."
            )

        elif final_score >= 60:

            return (
                "The candidate matches all detected technical "
                "skills, but the overall similarity score suggests "
                "that the resume could be improved by adding more "
                "role-specific keywords, projects, and measurable "
                "achievements."
            )

        else:

            return (
                "All detected technical skills are present, but "
                "the overall suitability score is relatively low. "
                "The candidate should strengthen the resume with "
                "more job-specific experience, projects, keywords, "
                "and measurable achievements."
            )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# UPLOAD RESUME
# ============================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_resume():

    file = request.files.get(
        "resume"
    )

    job_description = request.form.get(
        "job_description",
        ""
    )

    if not file or file.filename == "":
        return "Please select a resume."

    if not (
        file.filename.lower().endswith(".pdf")
        or
        file.filename.lower().endswith(".docx")
    ):

        return "Please upload a PDF or DOCX file."


    session["job_description"] = job_description


    filename = file.filename

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(file_path)


    # ========================================================
    # EXTRACT TEXT
    # ========================================================

    if filename.lower().endswith(".pdf"):

        extracted_text = extract_text_from_pdf(
            file_path
        )

    else:

        extracted_text = extract_text_from_docx(
            file_path
        )


    cleaned_text = clean_text(
        extracted_text
    )

    cleaned_job_description = clean_text(
        job_description
    )


    # ========================================================
    # SKILLS
    # ========================================================

    resume_skills = extract_skills(
        cleaned_text
    )

    job_skills = extract_skills(
        cleaned_job_description
    )


    matched_skills = [

        skill

        for skill in job_skills

        if skill in resume_skills

    ]


    missing_skills = [

        skill

        for skill in job_skills

        if skill not in resume_skills

    ]


    # ========================================================
    # SKILL MATCH
    # ========================================================

    if len(job_skills) > 0:

        match_percentage = (

            len(matched_skills)
            /
            len(job_skills)

        ) * 100

    else:

        match_percentage = 0


    # ========================================================
    # SIMILARITY
    # ========================================================

    similarity_score = calculate_similarity(

        cleaned_text,

        cleaned_job_description

    )


    # ========================================================
    # FINAL SCORE
    # ========================================================

    final_score = (

        (match_percentage * 0.5)
        +
        (similarity_score * 0.5)

    )


    # ========================================================
    # RECOMMENDATION
    # ========================================================

    if final_score >= 50:

        recommendation = "Shortlisted"

    else:

        recommendation = "Not Shortlisted"


    # ========================================================
    # SKILL GAP
    # ========================================================

    if missing_skills:

        if len(missing_skills) == 1:

            skill_gap_message = (
                "The candidate is missing 1 important "
                "job-related skill. Improving this skill "
                "could strengthen the candidate's profile."
            )

        else:

            skill_gap_message = (
                f"The candidate is missing "
                f"{len(missing_skills)} job-related skills. "
                "Developing these skills could improve "
                "their suitability for this role."
            )

    else:

        skill_gap_message = (
            "The candidate matches all detected technical "
            "skills required in the job description."
        )


    # ========================================================
    # AI IMPROVEMENT RECOMMENDATION
    # ========================================================

    improvement_recommendation = (
        generate_improvement_recommendation(
            matched_skills,
            missing_skills,
            match_percentage,
            similarity_score,
            final_score
        )
    )


    # ========================================================
    # PROFILE EXTRACTION
    # ========================================================

    education = extract_education(
        extracted_text
    )

    certifications = extract_certifications(
        extracted_text
    )

    experience = extract_experience(
        extracted_text
    )

    keywords = extract_keywords(
        cleaned_text
    )


    # ========================================================
    # DATABASE
    # ========================================================

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        """
        INSERT INTO resumes
        (
            filename,
            resume_text,
            cleaned_text
        )
        VALUES (%s, %s, %s)
        """,

        (
            filename,
            extracted_text,
            cleaned_text
        )

    )

    connection.commit()


    # ========================================================
    # GET NEW CANDIDATE ID
    # ========================================================

    candidate_id = cursor.lastrowid


    cursor.close()

    connection.close()


    # ========================================================
    # RESULT
    # ========================================================

    return render_template(

        "result.html",

        filename=filename,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        match_percentage=f"{match_percentage:.2f}",

        similarity_score=f"{similarity_score:.2f}",

        final_score=f"{final_score:.2f}",

        recommendation=recommendation,

        education=education,

        certifications=certifications,

        experience=experience,

        keywords=keywords,

        resume_text=extracted_text,

        candidate_id=candidate_id,

        skill_gap_message=skill_gap_message,

        improvement_recommendation=(
            improvement_recommendation
        )

    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route(
    "/dashboard",
    methods=["GET", "POST"]
)
def dashboard():

    # ========================================================
    # EMPTY DASHBOARD
    # ========================================================

    if request.method == "GET":

        return render_template(

            "dashboard.html",

            candidates=[],

            total_candidates=0,

            shortlisted=0,

            not_shortlisted=0,

            average_score="0.00",

            average_skill_match="0.00",

            average_similarity="0.00",

            top_candidate=None,

            shortlist_percentage="0.00",

            score_distribution=[]

        )


    # ========================================================
    # JOB DESCRIPTION
    # ========================================================

    job_description = request.form.get(
        "job_description",
        ""
    )


    if not job_description.strip():

        return "Please enter a job description."


    session["job_description"] = job_description


    cleaned_job_description = clean_text(
        job_description
    )

    job_skills = extract_skills(
        cleaned_job_description
    )


    # ========================================================
    # DATABASE
    # ========================================================

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        """
        SELECT
            id,
            filename,
            cleaned_text
        FROM resumes
        ORDER BY id
        """

    )

    resumes = cursor.fetchall()

    cursor.close()

    connection.close()


    candidates = []


    # ========================================================
    # ANALYZE CANDIDATES
    # ========================================================

    for resume in resumes:

        resume_id = resume[0]

        filename = resume[1]

        cleaned_text = resume[2]


        resume_skills = extract_skills(
            cleaned_text
        )


        matched_skills = [

            skill

            for skill in job_skills

            if skill in resume_skills

        ]


        if len(job_skills) > 0:

            match_percentage = (

                len(matched_skills)
                /
                len(job_skills)

            ) * 100

        else:

            match_percentage = 0


        similarity_score = calculate_similarity(

            cleaned_text,

            cleaned_job_description

        )


        final_score = (

            (match_percentage * 0.5)
            +
            (similarity_score * 0.5)

        )


        if final_score >= 50:

            recommendation = "Shortlisted"

        else:

            recommendation = "Not Shortlisted"


        candidates.append({

            "id": resume_id,

            "filename": filename,

            "skill_match": match_percentage,

            "similarity_score": similarity_score,

            "final_score": final_score,

            "recommendation": recommendation

        })


    # ========================================================
    # RANK CANDIDATES
    # ========================================================

    candidates = rank_candidates(
        candidates
    )


    # ========================================================
    # ANALYTICS
    # ========================================================

    total_candidates = len(
        candidates
    )


    shortlisted = sum(

        1

        for candidate in candidates

        if candidate["recommendation"]
        == "Shortlisted"

    )


    not_shortlisted = (

        total_candidates
        -
        shortlisted

    )


    # ========================================================
    # AVERAGES
    # ========================================================

    if total_candidates > 0:

        average_score = (

            sum(
                candidate["final_score"]
                for candidate in candidates
            )
            /
            total_candidates

        )


        average_skill_match = (

            sum(
                candidate["skill_match"]
                for candidate in candidates
            )
            /
            total_candidates

        )


        average_similarity = (

            sum(
                candidate["similarity_score"]
                for candidate in candidates
            )
            /
            total_candidates

        )

    else:

        average_score = 0

        average_skill_match = 0

        average_similarity = 0


    # ========================================================
    # SHORTLIST %
    # ========================================================

    if total_candidates > 0:

        shortlist_percentage = (

            shortlisted
            /
            total_candidates

        ) * 100

    else:

        shortlist_percentage = 0


    # ========================================================
    # TOP CANDIDATE
    # ========================================================

    if candidates:

        top_candidate = candidates[0]

    else:

        top_candidate = None


    # ========================================================
    # SCORE DISTRIBUTION
    # ========================================================

    score_distribution = [

        {

            "filename":
                candidate["filename"],

            "score":
                round(
                    candidate["final_score"],
                    2
                )

        }

        for candidate in candidates[:10]

    ]


    # ========================================================
    # DASHBOARD
    # ========================================================

    return render_template(

        "dashboard.html",

        candidates=candidates,

        total_candidates=total_candidates,

        shortlisted=shortlisted,

        not_shortlisted=not_shortlisted,

        average_score=f"{average_score:.2f}",

        average_skill_match=f"{average_skill_match:.2f}",

        average_similarity=f"{average_similarity:.2f}",

        top_candidate=top_candidate,

        shortlist_percentage=f"{shortlist_percentage:.2f}",

        score_distribution=score_distribution

    )


# ============================================================
# VIEW CANDIDATE PROFILE
# ============================================================

@app.route(
    "/candidate/<int:candidate_id>"
)
def candidate_profile(candidate_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        """
        SELECT
            id,
            filename,
            resume_text,
            cleaned_text
        FROM resumes
        WHERE id = %s
        """,

        (candidate_id,)

    )

    candidate = cursor.fetchone()

    cursor.close()

    connection.close()


    if not candidate:

        return "Candidate not found.", 404


    resume_id = candidate[0]

    filename = candidate[1]

    resume_text = candidate[2]

    cleaned_text = candidate[3]


    # ========================================================
    # PROFILE EXTRACTION
    # ========================================================

    resume_skills = extract_skills(
        cleaned_text
    )

    education = extract_education(
        resume_text
    )

    certifications = extract_certifications(
        resume_text
    )

    experience = extract_experience(
        resume_text
    )

    keywords = extract_keywords(
        cleaned_text
    )


    # ========================================================
    # JOB DESCRIPTION
    # ========================================================

    job_description = session.get(
        "job_description",
        ""
    )


    if job_description.strip():

        cleaned_job_description = clean_text(
            job_description
        )

        job_skills = extract_skills(
            cleaned_job_description
        )


        matched_skills = [

            skill

            for skill in job_skills

            if skill in resume_skills

        ]


        missing_skills = [

            skill

            for skill in job_skills

            if skill not in resume_skills

        ]


        if len(job_skills) > 0:

            match_percentage = (

                len(matched_skills)
                /
                len(job_skills)

            ) * 100

        else:

            match_percentage = 0


        similarity_score = calculate_similarity(

            cleaned_text,

            cleaned_job_description

        )


        final_score = (

            (match_percentage * 0.5)
            +
            (similarity_score * 0.5)

        )


        if final_score >= 50:

            recommendation = "Shortlisted"

        else:

            recommendation = "Not Shortlisted"


        if missing_skills:

            skill_gap_message = (

                f"The candidate is missing "
                f"{len(missing_skills)} "
                "job-related skill(s). "
                "Developing these skills could "
                "improve their suitability for this role."

            )

        else:

            skill_gap_message = (
                "The candidate matches all detected "
                "technical skills required in the "
                "job description."
            )


        # ====================================================
        # IMPROVEMENT RECOMMENDATION
        # ====================================================

        improvement_recommendation = (
            generate_improvement_recommendation(
                matched_skills,
                missing_skills,
                match_percentage,
                similarity_score,
                final_score
            )
        )


    else:

        matched_skills = resume_skills

        missing_skills = []

        match_percentage = 0

        similarity_score = 0

        final_score = 0

        recommendation = "Profile Viewed"

        skill_gap_message = (
            "Analyze this candidate against a job "
            "description to generate AI skill gap analysis."
        )

        improvement_recommendation = (
            "Provide a job description to generate "
            "personalized AI improvement recommendations."
        )


    # ========================================================
    # RESULT PAGE
    # ========================================================

    return render_template(

        "result.html",

        filename=filename,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        match_percentage=f"{match_percentage:.2f}",

        similarity_score=f"{similarity_score:.2f}",

        final_score=f"{final_score:.2f}",

        recommendation=recommendation,

        education=education,

        certifications=certifications,

        experience=experience,

        keywords=keywords,

        resume_text=resume_text,

        candidate_id=resume_id,

        skill_gap_message=skill_gap_message,

        improvement_recommendation=(
            improvement_recommendation
        )

    )


# ============================================================
# GENERATE PDF REPORT
# ============================================================

@app.route(
    "/candidate/<int:candidate_id>/report"
)
def candidate_report(candidate_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        """
        SELECT
            id,
            filename,
            resume_text,
            cleaned_text
        FROM resumes
        WHERE id = %s
        """,

        (candidate_id,)

    )

    candidate = cursor.fetchone()

    cursor.close()

    connection.close()


    if not candidate:

        return "Candidate not found.", 404


    filename = candidate[1]

    resume_text = candidate[2]

    cleaned_text = candidate[3]


    # ========================================================
    # EXTRACT
    # ========================================================

    resume_skills = extract_skills(
        cleaned_text
    )

    education = extract_education(
        resume_text
    )

    certifications = extract_certifications(
        resume_text
    )

    experience = extract_experience(
        resume_text
    )

    keywords = extract_keywords(
        cleaned_text
    )


    # ========================================================
    # JOB DESCRIPTION
    # ========================================================

    job_description = session.get(
        "job_description",
        ""
    )


    if job_description.strip():

        cleaned_job_description = clean_text(
            job_description
        )

        job_skills = extract_skills(
            cleaned_job_description
        )


        matched_skills = [

            skill

            for skill in job_skills

            if skill in resume_skills

        ]


        missing_skills = [

            skill

            for skill in job_skills

            if skill not in resume_skills

        ]


        if len(job_skills) > 0:

            match_percentage = (

                len(matched_skills)
                /
                len(job_skills)

            ) * 100

        else:

            match_percentage = 0


        similarity_score = calculate_similarity(

            cleaned_text,

            cleaned_job_description

        )


        final_score = (

            (match_percentage * 0.5)
            +
            (similarity_score * 0.5)

        )


        if final_score >= 50:

            recommendation = "Shortlisted"

        else:

            recommendation = "Not Shortlisted"


        if missing_skills:

            skill_gap_message = (

                f"The candidate is missing "
                f"{len(missing_skills)} "
                "job-related skill(s)."

            )

        else:

            skill_gap_message = (
                "The candidate matches all detected "
                "technical skills."
            )


        improvement_recommendation = (
            generate_improvement_recommendation(
                matched_skills,
                missing_skills,
                match_percentage,
                similarity_score,
                final_score
            )
        )


    else:

        matched_skills = resume_skills

        missing_skills = []

        match_percentage = 0

        similarity_score = 0

        final_score = 0

        recommendation = "Profile Viewed"

        skill_gap_message = (
            "No job description was provided."
        )

        improvement_recommendation = (
            "Provide a job description to generate "
            "personalized improvement recommendations."
        )


    # ========================================================
    # REPORT FOLDER
    # ========================================================

    report_folder = "reports"

    os.makedirs(
        report_folder,
        exist_ok=True
    )


    safe_filename = os.path.splitext(
        filename
    )[0]


    safe_filename = (

        safe_filename
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")

    )


    pdf_path = os.path.join(

        report_folder,

        f"{safe_filename}_AI_Report.pdf"

    )


    # ========================================================
    # PDF
    # ========================================================

    document = SimpleDocTemplate(

        pdf_path,

        pagesize=A4,

        rightMargin=40,

        leftMargin=40,

        topMargin=40,

        bottomMargin=40

    )


    styles = getSampleStyleSheet()

    title_style = styles["Title"]

    title_style.alignment = TA_CENTER

    heading_style = styles["Heading2"]

    normal_style = styles["BodyText"]


    story = []


    story.append(

        Paragraph(

            "AI RESUME SCREENING REPORT",

            title_style

        )

    )


    story.append(
        Spacer(1, 20)
    )


    story.append(

        Paragraph(

            "<b>Candidate:</b> "
            + escape(filename),

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # SCORE TABLE
    # ========================================================

    story.append(

        Paragraph(
            "AI SCORE ANALYSIS",
            heading_style
        )

    )


    score_data = [

        [
            "Metric",
            "Score"
        ],

        [
            "Skill Match",
            f"{match_percentage:.2f}%"
        ],

        [
            "Resume Similarity",
            f"{similarity_score:.2f}%"
        ],

        [
            "Overall AI Score",
            f"{final_score:.2f}%"
        ],

        [
            "Recommendation",
            recommendation
        ]

    ]


    score_table = Table(

        score_data,

        colWidths=[
            250,
            200
        ]

    )


    score_table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#4f46e5")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])

    )


    story.append(
        score_table
    )


    story.append(
        Spacer(1, 20)
    )


    # ========================================================
    # MATCHED SKILLS
    # ========================================================

    story.append(

        Paragraph(
            "MATCHED SKILLS",
            heading_style
        )

    )


    matched_text = (

        ", ".join(matched_skills)

        if matched_skills

        else

        "No matching skills detected."

    )


    story.append(

        Paragraph(

            escape(matched_text),

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # MISSING SKILLS
    # ========================================================

    story.append(

        Paragraph(
            "MISSING SKILLS",
            heading_style
        )

    )


    missing_text = (

        ", ".join(missing_skills)

        if missing_skills

        else

        "No major missing skills detected."

    )


    story.append(

        Paragraph(

            escape(missing_text),

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # AI SKILL GAP
    # ========================================================

    story.append(

        Paragraph(
            "AI SKILL GAP ANALYSIS",
            heading_style
        )

    )


    story.append(

        Paragraph(

            escape(skill_gap_message),

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # AI IMPROVEMENT RECOMMENDATION
    # ========================================================

    story.append(

        Paragraph(
            "AI IMPROVEMENT RECOMMENDATION",
            heading_style
        )

    )


    story.append(

        Paragraph(

            escape(
                improvement_recommendation
            ),

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # EDUCATION
    # ========================================================

    story.append(

        Paragraph(
            "EDUCATION",
            heading_style
        )

    )


    if education:

        education_text = "<br/>".join(

            escape(str(item))

            for item in education

        )

    else:

        education_text = (
            "No education information detected."
        )


    story.append(

        Paragraph(

            education_text,

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # EXPERIENCE
    # ========================================================

    story.append(

        Paragraph(
            "EXPERIENCE",
            heading_style
        )

    )


    if isinstance(experience, dict):

        experience_items = (

            experience.get(
                "sections",
                []
            )

            +

            experience.get(
                "date_ranges",
                []
            )

        )

    elif isinstance(experience, list):

        experience_items = experience

    else:

        experience_items = []


    if experience_items:

        experience_text = "<br/>".join(

            escape(str(item))

            for item in experience_items

        )

    else:

        experience_text = (
            "No detailed experience information detected."
        )


    story.append(

        Paragraph(

            experience_text,

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # CERTIFICATIONS
    # ========================================================

    story.append(

        Paragraph(
            "CERTIFICATIONS",
            heading_style
        )

    )


    if certifications:

        certification_text = "<br/>".join(

            escape(str(item))

            for item in certifications

        )

    else:

        certification_text = (
            "No certifications detected."
        )


    story.append(

        Paragraph(

            certification_text,

            normal_style

        )

    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # KEYWORDS
    # ========================================================

    story.append(

        Paragraph(
            "EXTRACTED KEYWORDS",
            heading_style
        )

    )


    keyword_text = (

        ", ".join(

            escape(str(keyword))

            for keyword in keywords[:50]

        )

        if keywords

        else

        "No keywords detected."

    )


    story.append(

        Paragraph(

            keyword_text,

            normal_style

        )

    )


    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story
    )


    # ========================================================
    # DOWNLOAD
    # ========================================================

    return send_file(

        pdf_path,

        as_attachment=True,

        download_name=(
            f"{safe_filename}_AI_Report.pdf"
        )

    )



# ============================================================
# CANDIDATE COMPARISON
# ============================================================

@app.route("/compare", methods=["GET", "POST"])
def compare_candidates():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            cleaned_text
        FROM resumes
        ORDER BY id
        """
    )

    resumes = cursor.fetchall()

    cursor.close()
    connection.close()

    candidates = []

    job_description = session.get(
        "job_description",
        ""
    )

    cleaned_job_description = clean_text(
        job_description
    )

    job_skills = extract_skills(
        cleaned_job_description
    )

    for resume in resumes:

        resume_id = resume[0]
        filename = resume[1]
        cleaned_text = resume[2]

        resume_skills = extract_skills(
            cleaned_text
        )

        matched_skills = [
            skill
            for skill in job_skills
            if skill in resume_skills
        ]

        if len(job_skills) > 0:
            skill_match = (
                len(matched_skills) / len(job_skills)
            ) * 100
        else:
            skill_match = 0

        similarity_score = calculate_similarity(
            cleaned_text,
            cleaned_job_description
        )

        final_score = (
            (skill_match * 0.5)
            + (similarity_score * 0.5)
        )

        recommendation = (
            "Shortlisted"
            if final_score >= 50
            else "Not Shortlisted"
        )

        candidates.append({
            "id": resume_id,
            "filename": filename,
            "skill_match": skill_match,
            "similarity_score": similarity_score,
            "final_score": final_score,
            "recommendation": recommendation
        })

    candidates.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    selected_candidates = []

    if request.method == "POST":

        selected_ids = request.form.getlist(
            "candidate_ids"
        )

        selected_ids = {
            int(candidate_id)
            for candidate_id in selected_ids
            if candidate_id.isdigit()
        }

        selected_candidates = [
            candidate
            for candidate in candidates
            if candidate["id"] in selected_ids
        ]

        selected_candidates.sort(
            key=lambda x: x["final_score"],
            reverse=True
        )

    return render_template(
        "compare.html",
        candidates=candidates,
        selected_candidates=selected_candidates
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )