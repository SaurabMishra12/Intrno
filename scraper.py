import re
import time
import requests
import requests_cache
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from duckduckgo_search import DDGS
import trafilatura

requests_cache.install_cache("research_cache", expire_after=3600)

RATE_LIMIT_SECONDS = 1.0
_last_request_time = 0.0


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = time.time()


def robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception:
        return False
    return rp.can_fetch("*", url)


def fetch_page(url: str) -> str:
    if not robots_allowed(url):
        return ""
    _rate_limit()
    response = requests.get(url, timeout=20, headers={"User-Agent": "AcademicResearcherDiscoveryBot/1.0"})
    response.raise_for_status()
    return response.text


def extract_emails(text: str):
    return sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))


def extract_profile_info(url: str) -> dict:
    html = fetch_page(url)
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    text = trafilatura.extract(html) or soup.get_text(" ", strip=True)
    emails = extract_emails(text)
    title = soup.title.string.strip() if soup.title else ""
    return {"title": title, "emails": emails, "text": text[:5000]}


def search_web(query: str, max_results: int = 5):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(r)
    return results


def find_researcher_links(name: str, institution: str = "") -> dict:
    query = f"{name} {institution} university homepage"
    results = search_web(query, max_results=5)
    homepage = results[0]["href"] if results else ""
    scholar = ""
    linkedin = ""
    for result in results:
        link = result.get("href", "")
        if "scholar.google" in link:
            scholar = link
        if "linkedin.com" in link:
            linkedin = link
    return {"homepage": homepage, "scholar": scholar, "linkedin": linkedin}


def enrich_researcher(name: str, institution: str = "") -> dict:
    links = find_researcher_links(name, institution)
    profile = extract_profile_info(links.get("homepage", "")) if links.get("homepage") else {}
    email = profile.get("emails", [""])[0] if profile.get("emails") else ""
    return {**links, "email": email}
