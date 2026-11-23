# OpenMind

Local-first scientific literature investigation prototype using Streamlit, OpenAlex, and Ollama.

## Setup (Windows CMD)

Install Python 3.11+ and Ollama, then:

```cmd
ollama pull qwen2.5:0.5b
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. The sidebar discovers installed Ollama models automatically.

## Current scope

- Search OpenAlex for papers and reconstruct available abstracts.
- Ask a local Ollama model to generate a cited, explicitly provisional research overview.
- Export reports and paper metadata.
- Show a clear warning when literature retrieval fails or returns zero results.
- No paid AI inference API required.

## Limitations

This is **not** a validated autonomous scientific discovery system. It does not run simulations or verify generated hypotheses experimentally. Paper metadata and abstracts may be incomplete; AI output can be inaccurate. OpenAlex retrieval requires internet. Google Drive streaming may cache models on the local disk. The 0.5B model is only suitable for basic testing.

## Troubleshooting

If Ollama responds with a 404, check that a model appears in `ollama list`. If literature search returns zero results, check internet connectivity and try a shorter scientific query.

## Word document AI editor

Upload a `.docx`, select a paragraph, rewrite with your installed Ollama model, review suggestions, and export a revised Word file.

```cmd
python -m pip install -r requirements.txt
python -m streamlit run word_editor.py
```

Open http://localhost:8501. For an existing local checkout run `git pull` first. The editor only rewrites selected body paragraphs; tables, headers, footers and text boxes are not editable. Formatting within rewritten paragraphs may be lost, so review the export. Use a capable model such as `qwen3:4b` for better writing quality.
