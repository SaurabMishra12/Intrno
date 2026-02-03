import re
from typing import List, Dict
import pdfplumber
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from llm_router import call_llm

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_skills_topics(text: str) -> Dict[str, List[str]]:
    keywords = set()
    for match in re.findall(r"\b[A-Za-z][A-Za-z\-\+]{2,}\b", text):
        if match.lower() in {"and", "the", "with", "from", "that", "this", "your", "for", "are"}:
            continue
        if match[0].isupper() or match.isupper():
            keywords.add(match)
    skills = sorted(keywords)
    methods = [k for k in skills if k.lower() in {"pytorch", "tensorflow", "scikit-learn", "nlp", "vision"}]
    topics = [k for k in skills if k not in methods]
    return {"skills": skills[:50], "methods": methods[:20], "topics": topics[:50]}


def build_interest_profile(text: str, extra_interests: List[str]) -> Dict[str, List[str]]:
    extracted = extract_skills_topics(text)
    interests = list(dict.fromkeys(extra_interests + extracted["topics"]))
    return {"skills": extracted["skills"], "methods": extracted["methods"], "topics": interests}


def ask_clarifying_questions(provider: str, model: str, api_key: str, text: str) -> str:
    prompt = (
        "You are an academic advisor. Based on the following background, ask 5 clarifying "
        "questions to better understand research interests.\n\n"
        f"Background:\n{text[:4000]}"
    )
    return call_llm(provider, model, api_key, prompt)


def refine_interest_vector(provider: str, model: str, api_key: str, profile: Dict[str, List[str]]) -> List[str]:
    prompt = (
        "Given the following list of skills and topics, return a refined list of 12 research "
        "areas as comma-separated phrases.\n"
        f"Skills: {', '.join(profile['skills'])}\n"
        f"Topics: {', '.join(profile['topics'])}"
    )
    response = call_llm(provider, model, api_key, prompt)
    return [item.strip() for item in response.split(",") if item.strip()]


def embed_texts(texts: List[str]):
    model = get_model()
    return model.encode(texts)


def similarity(a, b) -> float:
    return float(cosine_similarity([a], [b])[0][0])
