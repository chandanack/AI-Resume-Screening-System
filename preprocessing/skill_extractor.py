import re


# ============================================================
# TECHNICAL SKILLS
# ============================================================

SKILLS = [
    "python",
    "java",
    "c++",
    "c",
    "sql",
    "mysql",
    "mongodb",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data analysis",
    "data science",
    "data visualization",
    "natural language processing",
    "nlp",
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "flask",
    "django",
    "html",
    "css",
    "javascript",
    "react",
    "nodejs",
    "git",
    "github",
    "excel",
    "power bi",
    "tableau",
    "aws",
    "azure",
    "docker",
    "rest api",
    "api",
    "linux",
    "communication",
    "team leadership",
    "strategic planning",
    "sales",
    "customer relationship management"
]


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text):

    if not text:
        return []

    text = text.lower()

    found_skills = []

    for skill in SKILLS:

        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text):

            found_skills.append(skill)

    return found_skills


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

def extract_education(text):

    if not text:
        return []

    text = text.lower()

    education = []

    # Degree patterns
    degree_patterns = {
        "Bachelor of Engineering": [
            r"bachelor\s+of\s+engineering",
            r"\bb\.?\s*e\.?\b"
        ],

        "Bachelor of Technology": [
            r"bachelor\s+of\s+technology",
            r"\bb\.?\s*tech\.?\b",
            r"\bbtech\b"
        ],

        "Bachelor of Science": [
            r"bachelor\s+of\s+science",
            r"\bb\.?\s*sc\.?\b",
            r"\bbsc\b"
        ],

        "Bachelor of Computer Applications": [
            r"bachelor\s+of\s+computer\s+applications",
            r"\bbca\b"
        ],

        "Master of Engineering": [
            r"master\s+of\s+engineering"
        ],

        "Master of Technology": [
            r"master\s+of\s+technology",
            r"\bm\.?\s*tech\.?\b",
            r"\bmtech\b"
        ],

        "Master of Science": [
            r"master\s+of\s+science",
            r"\bm\.?\s*sc\.?\b",
            r"\bmsc\b"
        ],

        "Master of Computer Applications": [
            r"master\s+of\s+computer\s+applications",
            r"\bmca\b"
        ],

        "Master of Business Administration": [
            r"master\s+of\s+business\s+administration",
            r"\bmba\b"
        ],

        "PhD": [
            r"doctor\s+of\s+philosophy",
            r"\bph\.?\s*d\.?\b"
        ]
    }

    for degree, patterns in degree_patterns.items():

        for pattern in patterns:

            if re.search(pattern, text):

                if degree not in education:
                    education.append(degree)

                break


    # Branch / specialization
    branch_patterns = {
        "Artificial Intelligence and Machine Learning": [
            r"artificial intelligence\s+and\s+machine learning",
            r"artificial intelligence\s*&\s*machine learning",
            r"\bai\s*&\s*ml\b",
            r"\baiml\b"
        ],

        "Computer Science and Engineering": [
            r"computer science\s+and\s+engineering",
            r"computer science\s*&\s*engineering",
            r"\bcse\b"
        ],

        "Information Science and Engineering": [
            r"information science\s+and\s+engineering",
            r"\bise\b"
        ],

        "Electronics and Communication Engineering": [
            r"electronics\s+and\s+communication\s+engineering",
            r"\bece\b"
        ],

        "Mechanical Engineering": [
            r"mechanical engineering"
        ],

        "Civil Engineering": [
            r"civil engineering"
        ]
    }

    for branch, patterns in branch_patterns.items():

        for pattern in patterns:

            if re.search(pattern, text):

                if branch not in education:
                    education.append(branch)

                break


    # CGPA
    cgpa_patterns = [
        r"cgpa\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*/\s*10\s*cgpa",
        r"cgpa\s*(\d+(?:\.\d+)?)"
    ]

    for pattern in cgpa_patterns:

        match = re.search(pattern, text)

        if match:

            education.append(
                "CGPA: " + match.group(1) + "/10"
            )

            break


    # Academic duration
    year_match = re.search(
        r"\b(20\d{2})\s*[-–]\s*(20\d{2})\b",
        text
    )

    if year_match:

        education.append(
            "Duration: "
            + year_match.group(1)
            + " - "
            + year_match.group(2)
        )


    return education


# ============================================================
# CERTIFICATION EXTRACTION
# ============================================================

def extract_certifications(text):

    if not text:
        return []

    lines = text.splitlines()

    certifications = []

    in_certification_section = False

    certification_headers = [
        "certification",
        "certifications",
        "certificates",
        "courses",
        "training"
    ]

    stop_headers = [
        "experience",
        "education",
        "projects",
        "technical skills",
        "skills",
        "relevant coursework",
        "achievements"
    ]

    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            continue

        lower_line = clean_line.lower()


        # Start certification section
        if lower_line in certification_headers:

            in_certification_section = True

            continue


        # Stop certification section
        if in_certification_section:

            if lower_line in stop_headers:

                in_certification_section = False

                continue


        # Extract certification
        if in_certification_section:

            cleaned = re.sub(
                r"^[•\-\*\u2022]+\s*",
                "",
                clean_line
            )

            if len(cleaned) > 5:

                if cleaned not in certifications:

                    certifications.append(cleaned)


    return certifications


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience(text):

    if not text:

        return {
            "sections": [],
            "entries": []
        }


    lines = text.splitlines()

    sections = []

    entries = []

    in_experience_section = False


    experience_headers = [
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "work history",
        "career history"
    ]


    stop_headers = [
        "education",
        "projects",
        "technical skills",
        "skills",
        "certifications",
        "relevant coursework",
        "achievements"
    ]


    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            continue

        lower_line = clean_line.lower()


        # Start experience section
        if lower_line in experience_headers:

            in_experience_section = True

            if lower_line not in sections:

                sections.append(lower_line)

            continue


        # Stop experience section
        if in_experience_section:

            if lower_line in stop_headers:

                in_experience_section = False

                continue


        # Extract entries
        if in_experience_section:

            cleaned = re.sub(
                r"^[•\-\*\u2022]+\s*",
                "",
                clean_line
            )

            if len(cleaned) > 4:

                if cleaned not in entries:

                    entries.append(cleaned)


    # Look for common job/internship titles
    experience_keywords = [
        "intern",
        "internship",
        "developer",
        "engineer",
        "analyst",
        "manager"
    ]


    for line in lines:

        clean_line = line.strip()

        lower_line = clean_line.lower()


        if any(
            keyword in lower_line
            for keyword in experience_keywords
        ):

            if len(clean_line) > 4:

                if clean_line not in entries:

                    entries.append(clean_line)


    return {
        "sections": sections,
        "entries": entries[:20]
    }


# ============================================================
# KEYWORD EXTRACTION
# ============================================================

def extract_keywords(text):

    if not text:
        return []

    text = text.lower()

    words = re.findall(
        r"\b[a-zA-Z]{3,}\b",
        text
    )


    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "have",
        "has",
        "was",
        "were",
        "are",
        "you",
        "your",
        "our",
        "their",
        "into",
        "over",
        "about",
        "through",
        "using",
        "will",
        "been",
        "being",
        "also",
        "they",
        "them",
        "his",
        "her",
        "she",
        "who",
        "what",
        "where",
        "when"
    }


    keywords = []


    for word in words:

        if word not in stop_words:

            if word not in keywords:

                keywords.append(word)


    return keywords


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_features(text):

    skills = extract_skills(text)

    education = extract_education(text)

    certifications = extract_certifications(text)

    experience = extract_experience(text)

    keywords = extract_keywords(text)


    features = {
        "skill_count": len(skills),
        "education_count": len(education),
        "certification_count": len(certifications),
        "experience_count": len(experience["entries"]),
        "keyword_count": len(keywords)
    }


    return features