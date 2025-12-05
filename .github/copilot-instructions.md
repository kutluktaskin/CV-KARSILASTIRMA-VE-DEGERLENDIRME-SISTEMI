# Repository: CV-KARSILASTIRMA-VE-DEGERLENDIRME-SISTEMI

This file gives concise, actionable guidance for AI coding agents working on this repository.

- **Big picture**: This project reads PDF CVs, extracts structured sections (experience, education, skills, summary), creates semantic embeddings and compares CVs to produce a weighted compatibility score and a short HR-style report.

- **Main data flow (call chain)**:
  - `app.py` (Streamlit UI) -> calls `parse_cv(pdf_path)` in `cv_parser.py`
  - Parsed `sections` -> `extract_structured_data(sections)` in `data_extractor.py`
  - Structured data pairs -> `compare_cv_data(data_a, data_b)` in `comparison_engine.py`
  - `generate_report(...)` returns human-readable summary lines

- **Key files**:
  - `app.py`: Streamlit front-end; user interactions and file uploads.
  - `main.py`: CLI-style entry demonstrating same logic as `app.py` (non-UI runner).
  - `cv_parser.py`: PDF text extraction using `pdfplumber` and simple regex-based section splitting. Important functions: `extract_text_from_pdf`, `preprocess_text`, `extract_sections_simple`, `parse_cv`.
  - `data_extractor.py`: SpaCy-based extraction + rule-based heuristics. Important functions: `extract_structured_data`, `extract_skills`, `extract_experience_details`, `extract_education_details`. It attempts to load `en_core_web_sm` by default.
  - `comparison_engine.py`: Loads SBERT (`sentence-transformers`) model `all-MiniLM-L6-v2` and computes semantic similarity via `calculate_semantic_similarity` and `compare_cv_data`.

- **Third-party requirements** (discoverable from code):
  - `streamlit`, `spacy`, `pdfplumber`, `numpy`, `sentence-transformers`, `scikit-learn`, `torch` (runtime for sentence-transformers)
  - A `requirements.txt` has been added to the repo root listing these packages.

- **Important run/setup commands (Windows PowerShell)**
  - Create & activate venv (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

  - Install deps from repo root:

```powershell
pip install -r requirements.txt
```

  - Download spaCy model used by `data_extractor.py` (required):

```powershell
python -m spacy download en_core_web_sm
```

  - Start the UI (Streamlit):

```powershell
# from repo root after venv activation
python -m streamlit run app.py
```

  - Or run the non-UI flow for debugging:

```powershell
python main.py
```

- **Project-specific conventions & patterns**:
  - Section keys are expected in Turkish uppercase in many places: e.g. `DENEYİM`, `EĞİTİM`, `YETENEKLER`, `ÖZET`. Parsers attempt English fallbacks (e.g. `EXPERIENCE`, `SKILLS`). Keep those keys when manipulating structured data.
  - `data_extractor.py` uses SpaCy `nlp` globally; when adding new models, follow the existing fallback pattern (try custom -> fallback to `en_core_web_sm` -> set `nlp = None` on failure).
  - `comparison_engine.py` loads a global `SentenceTransformer` model once (heavy object). Reuse it rather than reloading per call.
  - `cv_parser.py` uses `pdfplumber` page-wise extraction and a regex-based `extract_sections_simple`. For improved OCR support, consider integrating `pytesseract` in `cv_parser.py` when `pdfplumber` text extraction returns empty pages.

- **Integration notes / gotchas**:
  - Sentence-Transformers (`all-MiniLM-L6-v2`) and `torch` will download model weights on first run — ensure Internet access or pre-cache the model.
  - spaCy models are separate packages; remember to run `python -m spacy download en_core_web_sm` after installing `spacy`.
  - If `SentenceTransformer` or `torch` fail to import, check the Python environment and that `pip install` was run inside the same venv used to run the app.
  - `parse_cv` returns section texts; downstream code expects some keys to exist, but functions defensively check for missing data — follow the pattern when adding new features.

- **Examples of common edits**:
  - To add a new section extraction (e.g., `SERTİFİKALAR`) add the title to `section_titles` in `cv_parser.py` and extractor logic in `data_extractor.py`.
  - To speed up semantic comparisons for many CVs, move `SEMANTIC_MODEL = SentenceTransformer(...)` to a shared startup path and pass the model instance into functions rather than using the global.

- **Debugging tips**:
  - If Streamlit fails to start: confirm you activated the same venv you installed packages into and that `streamlit` is importable in that environment.
  - If spaCy prints "model not found", run the `spacy download` command above. If you prefer another language model, update `CUSTOM_NER_MODEL_NAME` in `data_extractor.py`.
  - For embedding-related issues, run a quick script to import `sentence_transformers` and encode two sample sentences to validate the ML stack.

- **When making changes**:
  - Keep the public function names (`parse_cv`, `extract_structured_data`, `compare_cv_data`, `generate_report`) stable; the UI relies on them.
  - Add unit tests under a `tests/` folder and use small, deterministic examples (short JSON sections) to avoid heavy model loading during CI.

If any area here is unclear or you want the instructions extended (for example: CI setup, test commands, or Windows service deployment), tell me which part to expand and I'll update the document.