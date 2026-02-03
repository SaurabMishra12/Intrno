import requests
from typing import List, Dict
from urllib.parse import quote

ARXIV_URL = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_arxiv(query: str, max_results: int = 20) -> List[Dict]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    }
    response = requests.get(ARXIV_URL, params=params, timeout=30)
    response.raise_for_status()
    entries = response.text.split("<entry>")[1:]
    results = []
    for entry in entries:
        title = _extract_tag(entry, "title")
        summary = _extract_tag(entry, "summary")
        authors = [a.split("</name>")[0] for a in entry.split("<name>")[1:]]
        results.append({"title": title, "summary": summary, "authors": authors, "source": "arXiv"})
    return results


def search_semantic_scholar(query: str, limit: int = 20) -> List[Dict]:
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,url,publicationDate"
    }
    response = requests.get(SEMANTIC_SCHOLAR_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    results = []
    for paper in data.get("data", []):
        results.append({
            "title": paper.get("title"),
            "summary": paper.get("abstract") or "",
            "authors": [a.get("name") for a in paper.get("authors", [])],
            "url": paper.get("url"),
            "source": "Semantic Scholar",
        })
    return results


def _extract_tag(entry: str, tag: str) -> str:
    if f"<{tag}>" not in entry:
        return ""
    return entry.split(f"<{tag}>")[1].split(f"</{tag}>")[0].replace("\n", " ").strip()


def build_query(topics: List[str]) -> str:
    return " OR ".join([quote(t) for t in topics if t])
