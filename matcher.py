from typing import List, Dict
from nlp import embed_texts, similarity


def build_researcher_profiles(papers: List[Dict]) -> List[Dict]:
    profiles = {}
    for paper in papers:
        for author in paper.get("authors", []):
            entry = profiles.setdefault(author, {"name": author, "papers": [], "topics": []})
            entry["papers"].append(paper)
            if paper.get("title"):
                entry["topics"].append(paper["title"])
    return list(profiles.values())


def rank_researchers(researchers: List[Dict], interest_topics: List[str], countries: List[str]) -> List[Dict]:
    if not researchers:
        return []
    interest_embedding = embed_texts([" ".join(interest_topics)])[0]
    for researcher in researchers:
        combined = " ".join(researcher.get("topics", []))
        researcher_embedding = embed_texts([combined])[0]
        topic_score = similarity(interest_embedding, researcher_embedding)
        country_score = 0.1 if researcher.get("country") in countries else 0.0
        publication_score = min(len(researcher.get("papers", [])) / 10.0, 1.0)
        researcher["match_score"] = round(topic_score * 0.7 + publication_score * 0.2 + country_score * 0.1, 4)
    return sorted(researchers, key=lambda x: x["match_score"], reverse=True)
