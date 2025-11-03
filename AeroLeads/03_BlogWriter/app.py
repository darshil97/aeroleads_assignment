import os
import requests
import streamlit as st
from datetime import datetime
import re
import google.generativeai as genai
import io
import csv
import zipfile

st.set_page_config(page_title="AI Article Generator", layout="centered")

API_KEY = os.environ.get("GEMINI_API")

MODEL = "gemini-2.5-flash"  # prefer gemini-2.5-flash as requested


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\- ]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:50]


def generate_article(title: str, description: str, length_tokens: int, tone: str) -> str:
    """Generate article using the genai client and the configured MODEL.

    Raises RuntimeError if API key is missing or model call fails.
    """
    if not API_KEY:
        raise RuntimeError("GEMINI_API environment variable is not set.")

    prompt = f"Write a long-form article for the web based on the following title and optional description.\n\nTitle: {title}\n\n"
    if description:
        prompt += f"Description: {description}\n\n"

    prompt += (
        "Produce a well-structured article with an engaging introduction, subheadings, short paragraphs, "
        "a conclusion, a meta description (one sentence), 5 suggested tags (comma-separated), and an estimated "
        "reading time. Use a clear, human-like voice. Match the requested tone: "
        f"{tone}."
        f" Maximum length: approximately {length_tokens * 0.75:.0f} words."
    )

    # configure client (support different client versions)
    try:
        try:
            genai.configure(api_key=API_KEY)
        except Exception:
            try:
                genai.api_key = API_KEY
            except Exception:
                pass
    except Exception:
        # proceed; genai may still work without explicit configure call
        pass

    # Use the GenerativeModel API as requested
    try:
        model = genai.GenerativeModel(MODEL)
        # pass max_output_tokens when supported

        resp = model.generate_content(prompt)

        # Extract text from common shapes
        if resp is None:
            raise RuntimeError("Empty response from model.generate_content()")

        if hasattr(resp, "content") and resp.content:
            return resp.content
        if hasattr(resp, "text") and resp.text:
            return resp.text
        if hasattr(resp, "output") and resp.output:
            out = resp.output
            if isinstance(out, (list, tuple)) and len(out) > 0:
                first = out[0]
                if isinstance(first, dict) and "content" in first:
                    return first["content"]
                return str(first)
            return str(out)
        if isinstance(resp, dict):
            if "candidates" in resp and resp["candidates"]:
                return resp["candidates"][0].get("content") or resp["candidates"][0].get("output")
            if "output" in resp:
                return resp.get("output")

        # If none of the above, try common attributes for chat-like responses
        if hasattr(resp, "candidates") and len(resp.candidates) > 0:
            try:
                return resp.candidates[0].content
            except Exception:
                pass

        # Last resort: stringify
        return str(resp)

    except Exception as e:
        raise RuntimeError(f"Model generation failed: {e}")


def main():
    st.title("AI Article Generator")

    st.markdown(
        "Provide a title and optional description, choose length and tone, then click Generate to produce an article using the Gemini (Generative Language) API."
    )
    # Two tabs: Single and Bulk
    tab1, tab2 = st.tabs(["Single", "Bulk"])

    # Shared options
    with tab1:
        st.header("Single article")
        with st.form(key="generate_form"):
            title = st.text_input("Article title", max_chars=140)
            description = st.text_area("Description (optional)", height=80)
            length = st.selectbox("Length", ["Short (400 words)", "Medium (800 words)", "Long (1500+ words)"])
            tone = st.selectbox("Tone", ["Neutral", "Conversational", "Professional", "Persuasive", "Casual"])
            submit = st.form_submit_button("Generate")

        if submit:
            if not title:
                st.error("Please provide a title for the article.")
            else:
                length_map = {
                    "Short (400 words)": 600,
                    "Medium (800 words)": 1200,
                    "Long (1500+ words)": 2000,
                }
                tokens = length_map.get(length, 1200)

                spinner_text = "Generating article..."
                with st.spinner(spinner_text):
                    try:
                        article = generate_article(title.strip(), description.strip(), tokens, tone)
                    except Exception as e:
                        st.error(str(e))
                        article = None

                if article:
                    st.subheader("Generated article")
                    st.markdown(article)

                    # Provide metadata and download
                    now = datetime.now().strftime("%Y%m%d_%H%M")
                    filename = f"{slugify(title)}_{now}.md"
                    st.download_button("Download as Markdown", data=article, file_name=filename, mime="text/markdown")

                    st.success("Article generated — review and edit as needed.")

    with tab2:
        st.header("Bulk generate from CSV")
        st.write("Upload a CSV where the first column is the title and the second column is the description (description optional). If the file has a header row with 'title' or 'description', it will be skipped.")
        uploaded = st.file_uploader("Upload CSV file", type=["csv"])
        bulk_length = st.selectbox("Length for bulk items", ["Short (400 words)", "Medium (800 words)", "Long (1500+ words)"])
        bulk_tone = st.selectbox("Tone for bulk items", ["Neutral", "Conversational", "Professional", "Persuasive", "Casual"])
        process = st.button("Generate bulk articles")

        if process:
            if not uploaded:
                st.error("Please upload a CSV file to process.")
            else:
                # read CSV
                try:
                    data = uploaded.read().decode("utf-8-sig")
                except Exception:
                    data = uploaded.read().decode("utf-8")

                reader = csv.reader(io.StringIO(data))
                rows = list(reader)

                if len(rows) == 0:
                    st.error("Uploaded CSV is empty.")
                else:
                    # detect header
                    header = False
                    first = rows[0]
                    if len(first) >= 1 and isinstance(first[0], str) and first[0].strip().lower() in ("title", "headline"):
                        header = True
                    if len(first) >= 2 and isinstance(first[1], str) and first[1].strip().lower() in ("description", "desc"):
                        header = True

                    items = rows[1:] if header else rows

                    if len(items) == 0:
                        st.error("No data rows found in CSV after skipping header.")
                    else:
                        length_map = {
                            "Short (400 words)": 600,
                            "Medium (800 words)": 1200,
                            "Long (1500+ words)": 2000,
                        }
                        tokens = length_map.get(bulk_length, 1200)

                        zip_buffer = io.BytesIO()
                        success_count = 0
                        fail_items = []

                        progress = st.progress(0)
                        total = len(items)

                        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                            for idx, row in enumerate(items, start=1):
                                # defensive: skip empty rows
                                if not row or (len(row) == 1 and not row[0].strip()):
                                    progress.progress(int(idx / total * 100))
                                    continue

                                title = row[0].strip() if len(row) >= 1 else "Untitled"
                                description = row[1].strip() if len(row) >= 2 else ""

                                try:
                                    article = generate_article(title, description, tokens, bulk_tone)
                                    now = datetime.now().strftime("%Y%m%d_%H%M")
                                    fname = f"{slugify(title)}_{now}.md"
                                    # ensure unique filename in zip
                                    if fname in zf.namelist():
                                        fname = f"{slugify(title)}_{idx}_{now}.md"
                                    zf.writestr(fname, article)
                                    success_count += 1
                                except Exception as e:
                                    fail_items.append({"title": title, "error": str(e)})

                                progress.progress(int(idx / total * 100))

                        zip_buffer.seek(0)

                        if success_count == 0:
                            st.error("No articles were generated. See errors below.")
                        else:
                            st.success(f"Generated {success_count} articles; {len(fail_items)} failures.")
                            st.download_button("Download ZIP of articles", data=zip_buffer.getvalue(), file_name="generated_articles.zip", mime="application/zip")

                        if fail_items:
                            st.subheader("Failures")
                            for f in fail_items:
                                st.write(f"Title: **{f['title']}** — Error: {f['error']}")


if __name__ == "__main__":
    main()
