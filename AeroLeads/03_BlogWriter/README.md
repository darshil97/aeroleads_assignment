# AI Article Generator (Streamlit)

A small Streamlit app that generates articles using the Google Generative Language (Gemini) API.

## Setup

1. Create a Python environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your Gemini/Generative Language API key in the `GEMINI_API` environment variable. For example (macOS / zsh):

```bash
export GEMINI_API="YOUR_API_KEY_HERE"
```

You can also put the key in a `.env` file and use `python-dotenv` locally if preferred.

## Run

```bash
streamlit run app.py
```

Open the URL shown by Streamlit in your browser.

## Notes and tips

 - The app calls the `gemini-2.5-flash` model by default using the `google.generativeai` Python client when available. If you want a different model, change the `MODEL` constant in `app.py`.
- Keep an eye on token and quota usage for the Generative Language API.

