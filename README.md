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
