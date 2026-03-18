# streamlit_app.py
# InfoShield-AI — Streamlit Frontend
#
# FIXES applied vs original:
# 1. show_result() moved to TOP — was defined after it was called (NameError)
# 2. Image tab option name fixed: "Image" not "🖼️ Image" to match sidebar selectbox
# 3. uploaded_file.getvalue() used instead of read() — always returns full bytes
# 4. Signal breakdown added to show_result()
# 5. Backend health check added to sidebar
# 6. Connection error handling separated from generic errors
# 7. use_column_width removed — use width=700 instead
# 8. BACKEND_URL reads from env variable with localhost fallback
# 9. Timeout added to all requests (60s for image OCR)

import os
import io
import requests
import streamlit as st
from PIL import Image

# ===============================
# CONFIG
# ===============================
BACKEND_URL = os.environ.get("INFOSHIELD_BACKEND_URL", "http://localhost:5000/api")

st.set_page_config(
    page_title="InfoShield-AI",
    page_icon="🛡️",
    layout="wide"
)


# ===============================
# RESULT DISPLAY — defined first so all sections can call it
# ===============================
def show_result(data: dict):
    st.divider()

    label      = data.get("label", "UNKNOWN")
    confidence = data.get("confidence", 0.0)

    # Verdict banner
    col1, col2 = st.columns([2, 1])
    with col1:
        if label.upper() == "REAL":
            st.success(f"🟢 Verdict: **{label}**")
        elif label.upper() == "FAKE":
            st.error(f"🔴 Verdict: **{label}**")
        else:
            st.warning(f"⚠️ Verdict: **{label}**")
    with col2:
        st.metric("Confidence", f"{confidence * 100:.1f}%")

    # Signal breakdown
    signals = data.get("signals")
    if signals:
        st.subheader("📊 Signal Breakdown")
        s1, s2, s3 = st.columns(3)
        s1.metric("Zero-Shot Score",  f"{signals.get('zero_shot_score', 0):.2f}")
        s2.metric("Linguistic Score", f"{signals.get('linguistic_score', 0):.2f}")
        s3.metric("Evidence Score",   f"{signals.get('evidence_score', 0):.2f}")

    # Explanation
    st.subheader("🧠 Explanation")
    st.write(data.get("explanation", "No explanation available."))

    # Evidence
    st.subheader("📚 Evidence")
    evidence = data.get("evidence", [])
    if evidence:
        for ev in evidence:
            st.markdown(f"- {ev}")
    else:
        st.info("No matching evidence found in the knowledge base.")

    # OCR extracted text (image input only)
    if data.get("extracted_text"):
        with st.expander("🔍 Extracted Text (OCR)"):
            st.write(data["extracted_text"])
            if data.get("ocr_confidence"):
                st.caption(f"OCR confidence: {data['ocr_confidence'] * 100:.1f}%")

    # Source URL if available
    if data.get("source_url"):
        st.caption(f"Source: {data['source_url']}")


# ===============================
# HEADER
# ===============================
st.title("🛡️ InfoShield-AI")
st.caption("Agentic fake news detection — text, URLs, social media, and screenshots")


# ===============================
# SIDEBAR
# ===============================
option = st.sidebar.selectbox(
    "Choose Input Type",
    ["Text", "URL", "Image"]
)

with st.sidebar:
    st.divider()
    if st.button("🔍 Check Backend Status"):
        try:
            r = requests.get(
                f"{BACKEND_URL.replace('/api', '')}/health",
                timeout=5
            )
            if r.status_code == 200:
                st.success("Backend is running ✅")
            else:
                st.error(f"Backend returned {r.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Backend unreachable ❌\nRun: python app.py")
        except Exception as e:
            st.error(f"Error: {e}")


# ===============================
# TEXT INPUT
# ===============================
if option == "Text":
    st.header("📝 Analyze Text")
    st.info("Paste any news article, social media post, or claim to analyze.")

    text = st.text_area(
        "Enter news text",
        height=200,
        placeholder="e.g. Scientists confirm climate change is real based on NASA satellite data..."
    )

    if st.button("🔎 Analyze Text", type="primary", disabled=not text.strip()):
        with st.spinner("Analyzing..."):
            try:
                # Auto-detect URL pasted into text box
                if text.strip().startswith("http"):
                    response = requests.post(
                        f"{BACKEND_URL}/analyze-url",
                        json={"url": text.strip()},
                        timeout=60
                    )
                else:
                    response = requests.post(
                        f"{BACKEND_URL}/analyze",
                        json={"text": text.strip()},
                        timeout=60
                    )
                data = response.json()
                if response.status_code == 200:
                    show_result(data)
                else:
                    st.error(f"Error: {data.get('error', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure Flask is running:\n\npython app.py")
            except Exception as e:
                st.error(f"Unexpected error: {e}")


# ===============================
# URL INPUT
# ===============================
elif option == "URL":
    st.header("🔗 Analyze URL")
    st.info(
        "Supports news article URLs and Reddit posts. "
        "Twitter/X, Facebook, Instagram, and TikTok require login "
        "and cannot be scraped — paste the text directly instead."
    )

    url = st.text_input(
        "Enter a news or social media URL",
        placeholder="https://www.bbc.com/news/..."
    )

    if st.button("🔎 Analyze URL", type="primary", disabled=not url.strip()):
        with st.spinner("Extracting content & analyzing..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/analyze-url",
                    json={"url": url.strip()},
                    timeout=60
                )
                data = response.json()
                if response.status_code == 200:
                    show_result(data)
                else:
                    st.error(f"Error: {data.get('error', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure Flask is running:\n\npython app.py")
            except Exception as e:
                st.error(f"Unexpected error: {e}")


# ===============================
# IMAGE INPUT
# ===============================
elif option == "Image":
    st.header("🖼️ Analyze Screenshot / Image")
    st.info(
        "Upload a screenshot of a news headline or social media post. "
        "**Tip:** Save via Paint (Ctrl+V → Save As PNG) for best results."
    )

    uploaded_file = st.file_uploader(
        "Upload image",
        type=["png", "jpg", "jpeg", "bmp", "tiff", "webp"],
    )

    if uploaded_file:
        # getvalue() always returns complete bytes regardless of stream state
        img_bytes = uploaded_file.getvalue()

        # Display preview
        image = Image.open(io.BytesIO(img_bytes))
        st.image(image, caption="Uploaded image", width=700)
        st.caption(f"File: {uploaded_file.name} | Size: {len(img_bytes):,} bytes")

        if st.button("🔎 Analyze Image", type="primary"):
            with st.spinner("Running OCR + analysis..."):
                try:
                    files = {
                        "image": (
                            uploaded_file.name,
                            img_bytes,
                            uploaded_file.type or "image/png",
                        )
                    }
                    response = requests.post(
                        f"{BACKEND_URL}/analyze-image",
                        files=files,
                        timeout=60,
                    )
                    data = response.json()
                    if response.status_code == 200:
                        show_result(data)
                    else:
                        st.error(f"Error: {data.get('error', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure Flask is running:\n\npython app.py")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")