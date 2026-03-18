import streamlit as st
import requests
from PIL import Image
import io

def show_result(data):

    st.divider()

    # Label
    label = data.get("label", "Unknown")
    confidence = data.get("confidence", 0)

    if label.lower() == "real":
        st.success(f"🟢 {label}")
    else:
        st.error(f"🔴 {label}")

    # Confidence
    st.metric("Confidence", f"{confidence*100:.2f}%")

    # Explanation
    st.subheader("🧠 Explanation")
    st.write(data.get("explanation", ""))

    # Evidence
    st.subheader("📚 Evidence")
    evidence = data.get("evidence", [])

    if evidence:
        for ev in evidence:
            st.write(f"- {ev}")
    else:
        st.write("No evidence available")

    # Optional OCR text
    if "extracted_text" in data:
        st.subheader("🔍 Extracted Text")
        st.write(data["extracted_text"])
        
# ===============================
# 🔹 CONFIG
# ===============================
BACKEND_URL = "http://localhost:5000/api"

st.set_page_config(
    page_title="InfoShield-AI",
    page_icon="🛡️",
    layout="wide"
)

# ===============================
# 🔹 HEADER
# ===============================
st.title("🛡️ InfoShield-AI")
st.subheader("Fake News Detection System")

# ===============================
# 🔹 SIDEBAR
# ===============================
option = st.sidebar.selectbox(
    "Choose Input Type",
    ["Text", "URL", "Image"]
)

# ===============================
# 🔹 TEXT INPUT
# ===============================
if option == "Text":

    st.header("📝 Analyze Text")

    text = st.text_area("Enter news text", height=200)

    if st.button("Analyze Text"):

        if not text.strip():
            st.warning("Please enter text")
        else:
            with st.spinner("Analyzing..."):

                try:
                    if text.startswith("http"):
                        response = requests.post(f"{BACKEND_URL}/analyze-url", json={"url": text})
                    else:
                        response = requests.post(f"{BACKEND_URL}/analyze", json={"text": text})

                    data = response.json()

                    if response.status_code == 200:
                        show_result(data)
                    else:
                        st.error(data.get("error"))

                except Exception as e:
                    st.error(f"Backend not running: {e}")

# ===============================
# 🔹 URL INPUT
# ===============================
elif option == "URL":

    st.header("🔗 Analyze URL")

    url = st.text_input("Enter news or social media URL")

    if st.button("Analyze URL"):

        if not url.strip():
            st.warning("Please enter URL")
        else:
            with st.spinner("Extracting & analyzing..."):

                try:
                    response = requests.post(
                        f"{BACKEND_URL}/analyze-url",
                        json={"url": url}
                    )

                    data = response.json()

                    if response.status_code == 200:
                        show_result(data)
                    else:
                        st.error(data.get("error"))

                except Exception as e:
                    st.error(f"Backend not running: {e}")

# ===============================
# 🔹 IMAGE INPUT
# ===============================
elif option == "Image":

    st.header("🖼️ Analyze Screenshot")

    uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

    if uploaded_file:

        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", width=700)

        if st.button("Analyze Image"):

            with st.spinner("Processing OCR + Analysis..."):

                try:
                    files = {"image": uploaded_file.getvalue()}

                    response = requests.post(
                        f"{BACKEND_URL}/analyze-image",
                        files={"image": uploaded_file}
                    )

                    data = response.json()

                    if response.status_code == 200:
                        show_result(data)
                    else:
                        st.error(data.get("error"))

                except Exception as e:
                    st.error(f"Backend not running: {e}")

# ===============================
# 🔹 RESULT DISPLAY FUNCTION
# ===============================
