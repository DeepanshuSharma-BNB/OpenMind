import json
import re
import requests
import streamlit as st

st.set_page_config(page_title="OpenMind", page_icon="🔬", layout="wide")
st.title("🔬 OpenMind")
st.caption("Local-first scientific investigation. Generated hypotheses are not validated discoveries.")

def installed_models(url):
    response = requests.get(f"{url}/api/tags", timeout=8)
    response.raise_for_status()
    return [m["name"] for m in response.json().get("models", [])]

def reconstruct_abstract(inverted):
    if not inverted:
        return ""
    positions = {position: word for word, indices in inverted.items() for position in indices}
    return " ".join(positions[i] for i in sorted(positions))[:1500]

def search_papers(question, count):
    # Try a focused search before falling back to the original question.
    terms = re.findall(r"[A-Za-z0-9-]+", question)
    stop = {"what","when","where","which","was","were","are","the","and","their","first","all","fields","applications","potential","of","in","to","for","how","can","with","do","does","about"}
    query = " ".join(w for w in terms if w.lower() not in stop)[:180] or question
    response = requests.get(
        "https://api.openalex.org/works",
        params={"search": query, "per-page": count, "select": "id,title,publication_year,doi,abstract_inverted_index"},
        timeout=30,
    )
    response.raise_for_status()
    papers = []
    for item in response.json().get("results", []):
        papers.append({
            "title": item.get("title") or "Untitled",
            "year": item.get("publication_year"),
            "doi": item.get("doi"),
            "url": item.get("id"),
            "abstract": reconstruct_abstract(item.get("abstract_inverted_index")),
        })
    return papers, query

def generate(url, model, prompt):
    response = requests.post(
        f"{url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
        timeout=300,
    )
    if response.status_code == 404:
        raise ValueError(f"Model '{model}' not found in Ollama. Select an installed model in the sidebar.")
    response.raise_for_status()
    return response.json().get("response", "")

with st.sidebar:
    st.header("Local AI")
    url = st.text_input("Ollama server", "http://localhost:11434").rstrip("/")
    try:
        models = installed_models(url)
        if models:
            model = st.selectbox("Installed model", models)
            st.success(f"Connected: {len(models)} model(s) available")
        else:
            model = None
            st.warning("Ollama is reachable, but no models are installed.")
    except requests.RequestException as error:
        model = None
        st.error(f"Ollama unavailable: {error}")
    st.caption("Install a model with: ollama pull qwen2.5:0.5b")
    st.caption("Small models are suitable for connectivity tests, not reliable scientific conclusions.")

question = st.text_area("Your scientific question", height=110)
count = st.slider("Number of papers", 3, 15, 7)
if st.button("Investigate", type="primary", disabled=not question.strip() or model is None):
    st.session_state.pop("report", None)
    st.session_state.pop("papers", None)
    with st.status("Investigating...", expanded=True) as status:
        papers = []
        try:
            st.write("Searching OpenAlex...")
            papers, query = search_papers(question, count)
            st.write(f"Search terms: {query}")
            st.write(f"Retrieved {len(papers)} publications.")
        except requests.RequestException as error:
            st.warning(f"Literature retrieval failed: {error}")
        if not papers:
            status.update(label="No scientific evidence retrieved", state="error")
            st.error("No publications were retrieved. Check your internet connection or try a shorter question. No evidence-based report was generated.")
        else:
            sources = "\n".join(
                f"[{i}] {p['title']} ({p['year']}), {p['doi'] or p['url']}\nAbstract: {p['abstract'] or 'Unavailable'}"
                for i, p in enumerate(papers, 1)
            )
            prompt = (
                "You are a cautious scientific assistant. Use ONLY the listed metadata and abstracts as evidence. "
                "Do not invent citations or imply full-text access. Distinguish established findings, "
                "hypotheses, and unknowns. Cite source numbers [1], [2], etc. "
                "Sections: Research overview; Evidence; Testable hypotheses; Proposed computational tests; "
                "Experimental validation; Limitations.\n"
                f"Question: {question}\nSources:\n{sources}"
            )
            try:
                st.write(f"Consulting local model: {model}")
                st.session_state["report"] = generate(url, model, prompt)
                st.session_state["papers"] = papers
                status.update(label="Investigation completed", state="complete")
            except (requests.RequestException, ValueError) as error:
                status.update(label="AI generation failed", state="error")
                st.error(str(error))

if st.session_state.get("report"):
    st.subheader("Investigation report")
    st.markdown(st.session_state["report"])
    st.download_button("Download report", st.session_state["report"], "openmind_report.md", "text/markdown")
    st.subheader("Retrieved literature")
    for i, paper in enumerate(st.session_state.get("papers", []), 1):
        st.markdown(f"**[{i}] {paper['title']}** ({paper['year']})  \n{paper['doi'] or paper['url']}")
    st.download_button("Download source metadata", json.dumps(st.session_state["papers"], indent=2), "sources.json", "application/json")
