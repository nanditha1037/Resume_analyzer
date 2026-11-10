import io
import re
from django.shortcuts import render
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer, util

# Load the AI model once, when the server starts
model = SentenceTransformer("all-MiniLM-L6-v2")

# Known skills. Only these are looked for, so random words never appear.
SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "rust",
    "kotlin", "swift", "php", "ruby", "r", "matlab", "scala", "bash",
    # Web
    "html", "css", "react", "angular", "vue", "node.js", "express", "django",
    "flask", "fastapi", "spring boot", "bootstrap", "tailwind", "rest api",
    "graphql", "jquery", "next.js",
    # Data
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "redis", "firebase",
    "pandas", "numpy", "matplotlib", "seaborn", "power bi", "tableau", "excel",
    "data cleaning", "data analysis", "data visualization", "data science",
    "data engineering", "etl", "statistics", "big data", "spark", "hadoop",
    "data preprocessing", "feature engineering",
    # AI / ML
    "machine learning", "deep learning", "neural networks", "nlp",
    "natural language processing", "computer vision", "tensorflow", "pytorch",
    "keras", "scikit-learn", "opencv", "transformers", "llm", "generative ai",
    "reinforcement learning", "cnn", "rnn", "lstm", "yolo", "hugging face",
    "langchain", "prompt engineering", "mlops", "model deployment",
    "speech recognition", "text to speech",
    # Tools and cloud
    "git", "github", "docker", "kubernetes", "linux", "aws", "azure",
    "google cloud", "jenkins", "ci/cd", "jira", "postman", "vs code",
    "jupyter", "google colab", "streamlit", "gradio",
    # CS fundamentals
    "data structures", "algorithms", "object oriented programming", "oop",
    "operating systems", "computer networks", "dbms", "system design",
    "design patterns", "multithreading",
    # Software practice
    "agile", "scrum", "unit testing", "debugging", "version control",
    "api development", "web development", "software development",
    "full stack", "backend", "frontend",
    # Soft skills
    "problem solving", "communication", "teamwork", "leadership",
    "time management", "critical thinking",
]

# Extra spellings that mean the same skill
ALIASES = {
    "scikit learn": "scikit-learn", "sklearn": "scikit-learn",
    "nodejs": "node.js", "node js": "node.js", "reactjs": "react",
    "postgres": "postgresql", "js": "javascript", "ml": "machine learning",
    "dl": "deep learning", "natural language processing": "nlp",
    "object-oriented programming": "object oriented programming",
    "rest apis": "rest api", "restful api": "rest api", "tf": "tensorflow",
}

# Short advice for missing skills
TIPS = {
    "python": "Build one small project in Python and push it to GitHub.",
    "sql": "Practice SQL queries on a free dataset and add one project that uses a database.",
    "machine learning": "Train a simple model with scikit-learn and document the results.",
    "deep learning": "Build a small image or text classifier with TensorFlow or PyTorch.",
    "git": "Create a GitHub profile and commit your projects regularly.",
    "github": "Create a GitHub profile and commit your projects regularly.",
    "docker": "Containerize one of your projects with a simple Dockerfile.",
    "django": "Build a small Django app with forms and a database.",
    "flask": "Build a small Flask API with two or three routes.",
    "nlp": "Try a text classification or sentiment analysis mini project.",
    "tensorflow": "Follow the official beginner tutorial and publish the notebook.",
    "pytorch": "Follow the official 60-minute blitz and publish the notebook.",
    "aws": "Deploy a small app on the AWS free tier.",
    "data structures": "Solve 30 to 50 practice problems and mention the platform.",
    "algorithms": "Solve 30 to 50 practice problems and mention the platform.",
}


def extract_pdf(data):
    reader = PdfReader(io.BytesIO(data))
    return " ".join(page.extract_text() or "" for page in reader.pages)


def extract_docx(data):
    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return " ".join(parts)


def extract_text(file):
    """Read text from an uploaded PDF or Word file."""
    file.seek(0)
    data = file.read()
    name = file.name.lower()
    if name.endswith(".pdf"):
        return extract_pdf(data)
    if name.endswith(".docx"):
        return extract_docx(data)
    raise ValueError("Unsupported file type")


def normalize(text):
    """Lowercase and replace aliases with the main skill name."""
    text = " " + re.sub(r"\s+", " ", text.lower()) + " "
    for alias, main in ALIASES.items():
        text = re.sub(r"(?<![a-z0-9+#.])" + re.escape(alias) + r"(?![a-z0-9+#])", " " + main + " ", text)
    return text


def find_skills(text):
    """Return the set of known skills that appear in the text."""
    text = normalize(text)
    found = set()
    for skill in SKILLS:
        pattern = r"(?<![a-z0-9+#.])" + re.escape(skill) + r"(?![a-z0-9+#])"
        if re.search(pattern, text):
            found.add(skill)
    return found


def display(skill):
    """Make skills look nice on screen."""
    special = {
        "nlp": "NLP", "sql": "SQL", "html": "HTML", "css": "CSS", "aws": "AWS",
        "llm": "LLM", "cnn": "CNN", "rnn": "RNN", "lstm": "LSTM", "yolo": "YOLO",
        "oop": "OOP", "etl": "ETL", "dbms": "DBMS", "ci/cd": "CI/CD",
        "rest api": "REST API", "mysql": "MySQL", "postgresql": "PostgreSQL",
        "mongodb": "MongoDB", "github": "GitHub", "tensorflow": "TensorFlow",
        "pytorch": "PyTorch", "opencv": "OpenCV", "node.js": "Node.js",
        "next.js": "Next.js", "power bi": "Power BI", "vs code": "VS Code",
        "scikit-learn": "scikit-learn", "mlops": "MLOps", "graphql": "GraphQL",
        "javascript": "JavaScript", "typescript": "TypeScript",
        "fastapi": "FastAPI", "jquery": "jQuery", "c++": "C++", "c#": "C#",
    }
    return special.get(skill, skill.title())


def analyze(resume, jd):
    """Compare skills and overall meaning."""
    jd_skills = find_skills(jd)
    resume_skills = find_skills(resume)

    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)

    # Overall meaning similarity from the AI model
    emb = model.encode([resume[:6000], jd[:6000]], convert_to_tensor=True)
    overall = max(float(util.cos_sim(emb[0], emb[1])), 0.0)

    if jd_skills:
        coverage = len(matched) / len(jd_skills)
        # 60% skill coverage + 40% AI meaning
        final = (0.6 * coverage + 0.4 * overall) * 100
    else:
        final = overall * 100

    tips = []
    for skill in missing[:5]:
        tips.append(f"{display(skill)}: " + TIPS.get(skill, "Add it to your skills or a project, if you have used it."))

    return round(final, 1), [display(s) for s in matched], [display(s) for s in missing], tips, len(jd_skills)


def get_summary(score):
    if score < 30:
        return "Low match. This job is quite different from your resume. Look for roles closer to your skills."
    if score < 55:
        return "Average match. Add the missing skills to your projects and skills section, if they are true for you."
    return "Strong match! Fine-tune the wording and quantify your achievements."


def home(request):
    context = {}
    if request.method == "POST":
        resume = request.FILES.get("resume")
        jd = request.POST.get("jd", "").strip()
        if resume and jd:
            if not resume.name.lower().endswith((".pdf", ".docx")):
                context = {"error": "Please upload a PDF or Word (.docx) file."}
            else:
                try:
                    text = extract_text(resume)
                    if not text.strip():
                        context = {"error": "No readable text found in this file. Try a text-based PDF or a Word file."}
                    else:
                        score, matched, missing, tips, total = analyze(text, jd)
                        context = {
                            "score": score,
                            "matched": matched,
                            "missing": missing,
                            "tips": tips,
                            "total": total,
                            "tip": get_summary(score),
                        }
                except Exception as e:
                    context = {"error": f"Error: {type(e).__name__}: {e}"}
        else:
            context = {"error": "Please upload a resume and paste a job description."}
    return render(request, "analyzer/home.html", context)