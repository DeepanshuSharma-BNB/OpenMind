"""OpenMind Word Editor: local document rewriting with Ollama."""
import io
import json
import re
import requests
import streamlit as st
from docx import Document

st.set_page_config(page_title="OpenMind Word Editor", page_icon="📝", layout="wide")
st.title("📝 OpenMind | Word Editor")
st.caption("Private, local-first document editing powered by Ollama. Review every change before exporting.")

@st.cache_data(show_spinner=False)
def load_docx(data):
    doc = Document(io.BytesIO(data))
    return [(i, p.text, p.style.name) for i, p in enumerate(doc.paragraphs) if p.text.strip()]

def models_at(url):
    r = requests.get(url + "/api/tags", timeout=8)
    r.raise_for_status()
    return [m["name"] for m in r.json().get("models", [])]

def ask_ollama(url, model, original, instruction):
    prompt = (
        "You are a careful professional copy editor. Rewrite the supplied paragraph following the user's instruction. "
        "Preserve technical meaning, citations, numbers, terminology, units, and factual claims. "
        "Do not invent references, evidence, or findings. "
        "Return ONLY a JSON object with keys rewritten (string) and suggestions (array of 2 to 5 short strings). "
        "Do not wrap in markdown.\n"
        "Instruction: " + instruction + "\nParagraph:\n" + original
    )
    r = requests.post(url + "/api/chat", json={
        "model": model, "stream": False, "format": "json",
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0.2}
    }, timeout=300)
    if r.status_code == 404:
        raise ValueError("The selected model was not found. Choose an installed Ollama model.")
    r.raise_for_status()
    answer = json.loads(r.json()["message"]["content"])
    rewritten = answer.get("rewritten", "")
    suggestions = answer.get("suggestions", [])
    if not isinstance(rewritten, str) or not rewritten.strip():
        raise ValueError("The AI did not return a valid rewrite.")
    if not isinstance(suggestions, list):
        suggestions = []
    return rewritten.strip(), [str(s) for s in suggestions[:5]]

with st.sidebar:
    st.header("Local AI")
    url = st.text_input("Ollama server", "http://localhost:11434").rstrip("/")
    try:
        models = models_at(url)
        model = st.selectbox("Installed model", models) if models else None
        if model:
            st.success("Connected to Ollama")
        else:
            st.warning("No models installed. Run: ollama pull qwen3:4b")
    except requests.RequestException as e:
        model = None
        st.error(f"Ollama unavailable: {e}")
    st.caption("No paid API credits required. The document stays on this machine unless you deploy the app elsewhere.")

uploaded = st.file_uploader("Upload a Word document", type=["docx"])
if uploaded:
    data = uploaded.getvalue()
    file_key = str(hash(data))
    if st.session_state.get("file_key") != file_key:
        st.session_state["file_key"] = file_key
        st.session_state["edits"] = {}
        st.session_state["suggestions"] = {}
    try:
        paragraphs = load_docx(data)
    except Exception as e:
        st.error(f"Could not read this Word file: {e}")
        st.stop()
    if not paragraphs:
        st.warning("No editable body paragraphs were found. Text in tables, headers, and text boxes is not supported yet.")
        st.stop()
    st.write(f"Found {len(paragraphs)} nonempty body paragraphs.")
    choices = {f"{i+1}. {text[:105]}{'…' if len(text)>105 else ''}": i for i, text, style in paragraphs}
    selected_label = st.selectbox("Select a paragraph", list(choices))
    index = choices[selected_label]
    original = next(t for i, t, s in paragraphs if i == index)
    instruction = st.selectbox("Editing goal", [
        "Improve clarity and flow", "Scientific and academic writing",
        "Fix grammar and spelling", "Make concise", "Make more natural",
        "Improve formal professional tone", "Custom instruction"
    ])
    custom = st.text_input("Your instruction", placeholder="Describe how you want the paragraph changed") if instruction == "Custom instruction" else ""
    goal = custom.strip() if instruction == "Custom instruction" else instruction
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.text_area("Source paragraph", original, height=230, disabled=True)
    with col2:
        st.subheader("Proposed revision")
        draft = st.session_state["edits"].get(index, original)
        edited = st.text_area("Editable revision", draft, height=230, key=f"revision_{file_key}_{index}_{hash(draft)}")
        if edited != draft:
            st.session_state["edits"][index] = edited
    if st.button("Rewrite and suggest", type="primary", disabled=not model or not goal):
        with st.spinner("Rewriting with your local AI model..."):
            try:
                revision, tips = ask_ollama(url, model, original, goal)
                st.session_state["edits"][index] = revision
                st.session_state["suggestions"][index] = tips
                st.rerun()
            except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as e:
                st.error(f"Could not rewrite paragraph: {e}")
    tips = st.session_state["suggestions"].get(index, [])
    if tips:
        st.subheader("Editing suggestions")
        for tip in tips:
            st.write("• " + tip)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Keep original paragraph"):
            st.session_state["edits"].pop(index, None)
            st.session_state["suggestions"].pop(index, None)
            st.rerun()
    with c2:
        st.metric("Paragraphs with proposed edits", len(st.session_state["edits"]))
    st.divider()
    st.subheader("Export")
    st.caption("Only edited body paragraphs are replaced. Existing paragraph styles and untouched sections remain, but inline formatting within rewritten paragraphs (bold, italic, hyperlinks, etc.) may be lost. Review the exported file.")
    if st.button("Prepare revised Word document"):
        doc = Document(io.BytesIO(data))
        for idx, replacement in st.session_state["edits"].items():
            doc.paragraphs[idx].text = replacement
        output = io.BytesIO()
        doc.save(output)
        st.session_state["export_bytes"] = output.getvalue()
    if st.session_state.get("export_bytes"):
        st.download_button("Download revised .docx", st.session_state["export_bytes"],
                           file_name="OpenMind_revised.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
else:
    st.info("Upload a .docx file to begin. Legacy .doc files are not supported.")
