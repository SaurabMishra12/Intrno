import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from nlp import extract_text_from_pdf, build_interest_profile, ask_clarifying_questions, refine_interest_vector
from search import search_arxiv, search_semantic_scholar
from matcher import build_researcher_profiles, rank_researchers
from scraper import enrich_researcher
from llm_router import redact_key
from db import init_db, save_session, save_results, get_results, list_sessions, save_alert
from pyvis.network import Network

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def generate_graph(researchers):
    net = Network(height="500px", width="100%", bgcolor="#ffffff")
    for researcher in researchers:
        net.add_node(researcher["name"], label=researcher["name"])
        for paper in researcher.get("papers", [])[:3]:
            title = paper.get("title", "Paper")
            net.add_node(title, label=title, color="#97c2fc")
            net.add_edge(researcher["name"], title)
    output_path = os.path.join("static", "graph.html")
    net.write_html(output_path)
    return output_path


@app.route("/")
def home():
    sessions = list_sessions()
    return render_template("home.html", sessions=sessions)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        interests = request.form.get("interests", "").split(",")
        interests = [i.strip() for i in interests if i.strip()]
        countries = request.form.getlist("countries")
        provider = request.form.get("provider")
        model = request.form.get("model")
        api_key = request.form.get("api_key")
        session["api_key"] = api_key
        session["provider"] = provider
        session["model"] = model

        text = ""
        if "resume" in request.files:
            resume = request.files["resume"]
            if resume.filename:
                path = os.path.join(UPLOAD_FOLDER, resume.filename)
                resume.save(path)
                text = extract_text_from_pdf(path)
        website = request.form.get("website")
        if website:
            text += f"\nWebsite: {website}"

        profile = build_interest_profile(text, interests)
        if provider and api_key:
            questions = ask_clarifying_questions(provider, model, api_key, text)
            refined = refine_interest_vector(provider, model, api_key, profile)
        else:
            questions = "Provide any additional research interests or methods you'd like to emphasize."
            refined = profile["topics"]

        session_id = save_session(profile, countries, provider, model)
        session["session_id"] = session_id
        session["profile"] = profile
        session["refined"] = refined
        return render_template("llm_config.html", questions=questions, refined=refined)
    return render_template("upload.html")


@app.route("/results", methods=["POST"])
def results():
    session_id = session.get("session_id")
    profile = session.get("profile", {})
    refined_input = request.form.get("refined", "")
    refined = [item.strip() for item in refined_input.split(",") if item.strip()] or session.get("refined", [])
    countries = request.form.getlist("countries") or []
    if not refined:
        refined = profile.get("topics", [])

    query = " ".join(refined)
    papers = search_arxiv(query, max_results=15) + search_semantic_scholar(query, limit=15)
    researchers = build_researcher_profiles(papers)
    for researcher in researchers:
        enrichment = enrich_researcher(researcher["name"], researcher.get("institution", ""))
        researcher.update(enrichment)
        researcher["research_areas"] = refined[:5]
        researcher["top_papers"] = [p.get("title") for p in researcher.get("papers", [])[:3]]
        researcher["country"] = researcher.get("country", "")
        researcher["institution"] = researcher.get("institution", "")
    ranked = rank_researchers(researchers, refined, countries)
    save_results(session_id, ranked)
    graph_path = generate_graph(ranked[:10]) if ranked else ""
    return render_template("results.html", researchers=ranked, graph_path=graph_path)


@app.route("/professor/<int:index>")
def professor(index):
    session_id = session.get("session_id")
    results = get_results(session_id)
    if index < 0 or index >= len(results):
        return redirect(url_for("home"))
    professor = results[index]
    return render_template("profile.html", professor=professor, index=index)


@app.route("/export/csv")
def export_csv():
    session_id = session.get("session_id")
    results = get_results(session_id)
    df = pd.DataFrame(results)
    path = "researchers.csv"
    df.to_csv(path, index=False)
    return send_file(path, as_attachment=True)


@app.route("/export/pdf")
def export_pdf():
    session_id = session.get("session_id")
    results = get_results(session_id)
    path = "researchers.pdf"
    c = canvas.Canvas(path, pagesize=letter)
    y = 750
    for researcher in results:
        c.drawString(50, y, f"{researcher['name']} - {researcher.get('institution', '')}")
        y -= 20
        if y < 100:
            c.showPage()
            y = 750
    c.save()
    return send_file(path, as_attachment=True)


@app.route("/alerts")
def alerts():
    flash("Weekly alert system is active and will check for new matches.")
    return redirect(url_for("home"))


@app.route("/generate-email", methods=["POST"])
def generate_email():
    provider = session.get("provider")
    model = session.get("model")
    api_key = session.get("api_key")
    professor = request.form.get("professor")
    profile = session.get("profile", {})
    prompt = (
        "Draft a concise, professional cold email to a professor about research fit. "
        f"Professor: {professor}. Student interests: {', '.join(profile.get('topics', []))}."
    )
    if provider and api_key:
        from llm_router import call_llm
        email = call_llm(provider, model, api_key, prompt)
    else:
        email = "Please configure an LLM provider to generate a custom email."
    return {"email": email}


@app.context_processor
def inject_globals():
    return {"redacted_api_key": redact_key(session.get("api_key", ""))}


def schedule_weekly_alerts():
    sessions = list_sessions()
    for s in sessions:
        save_alert(s["id"], "Weekly check completed - review new matches.")


if __name__ == "__main__":
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(schedule_weekly_alerts, "interval", days=7, next_run_time=datetime.utcnow())
    scheduler.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
