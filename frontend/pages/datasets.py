import streamlit as st
from frontend.utils.api_client import APIClient

st.title("My Datasets")

client = APIClient()

if "access_token" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

# File upload section
uploaded_file = st.file_uploader("Upload a new CSV dataset", type="csv")
if uploaded_file:
    if st.button("Confirm Upload"):
        with st.spinner("Uploading and analyzing..."):
            try:
                res = client.upload_dataset(uploaded_file.getvalue(), uploaded_file.name)
                if res and "id" in res:
                    st.success(f"File {uploaded_file.name} uploaded successfully!")
                else:
                    st.error("Upload failed: Invalid server response.")
            except Exception as e:
                st.error(f"Upload failed: {e}")

st.divider()

# List available datasets
st.subheader("Available Datasets")
try:
    datasets = client.list_datasets()
except Exception as e:
    st.error(f"Failed to load datasets: {e}")
    datasets = []

if datasets:
    for ds in datasets:
        with st.expander(f"📁 {ds['filename']}"):
            st.write(f"**Uploaded at:** {ds['uploaded_at']}")
            st.write(f"**Rows:** {ds['row_count']}")
            if ds['column_info']:
                st.write("**Columns:**")
                st.json(ds['column_info'])
else:
    st.info("No datasets available. Please upload one above.")
