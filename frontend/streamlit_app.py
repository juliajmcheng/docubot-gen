import streamlit as st
import requests

st.set_page_config(page_title="DocuBot", layout="centered")
st.title("📄 DocuBot – Ask Questions About Your PDF")

# Store upload state
if "pdf_uploaded" not in st.session_state:
    st.session_state["pdf_uploaded"] = False

# Step 1: Upload PDF
st.subheader("Step 1: Upload your PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# Only upload and process once
if uploaded_file and not st.session_state["pdf_uploaded"]:
    with st.spinner("Uploading and processing..."):
        res = requests.post(
            "http://localhost:8000/upload/",
            files={"file": uploaded_file}
        )
        if res.status_code == 200:
            res_json = res.json()
            st.success("PDF processed successfully!")
            st.session_state["pdf_uploaded"] = True

            # 👇 Display the title returned by backend
            title = res_json.get("title", "Unknown title")
            st.info(f"📄 **Extracted Title:** {title}")
        else:
            st.error("Upload failed. Please check backend status.")

# Step 2: Ask a Question (always show)
st.subheader("Step 2: Ask a question")
question = st.text_input("Enter your question about the PDF")

if st.button("Ask"):
    if not st.session_state["pdf_uploaded"]:
        st.warning("Please upload a PDF first.")
    elif not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            res = requests.post(
                "http://localhost:8000/ask/",
                data={"query": question}
            )
            if res.status_code == 200:
                answer = res.json().get("answer", "")
                st.success("Answer:")
                st.write(answer)
            else:
                st.error("Something went wrong while querying.")
