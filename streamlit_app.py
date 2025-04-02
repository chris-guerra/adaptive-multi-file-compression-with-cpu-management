import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"  # Ensure this matches your FastAPI port

def process_files(files, compression_level, threads, decompress):
    """Send files to the backend for processing."""
    params = {
        "compression_level": compression_level,
        "threads": threads,
        "decompress": decompress,
    }
    file_data = [("files", (file.name, file)) for file in files]
    response = requests.post(f"{API_BASE_URL}/process/files", params=params, files=file_data)
    response.raise_for_status()
    return response.json()

def get_download_data():
    """Fetch the processed file(s) for download."""
    download_url = f"{API_BASE_URL}/download_all"
    response = requests.get(download_url)
    response.raise_for_status()
    return response.content

# Use a placeholder for the download button in the sidebar
download_placeholder = st.sidebar.empty()

# Initialize session state for file readiness if not set
if "files_ready" not in st.session_state:
    st.session_state["files_ready"] = False

# Sidebar: Options
st.sidebar.title("Options")
compression_level = st.sidebar.slider("Compression Level", 1, 9, 6)
threads = st.sidebar.number_input("Threads", 1, 32, 8)
decompress = st.sidebar.checkbox("Decompress Instead of Compress", value=False)

# Main Window: Title and Upload Instructions
st.title("File Compressor")
st.markdown("### Drag and drop files here")
st.markdown("**No file size limit**")

# Main Window: File Upload
uploaded_files = st.file_uploader(
    "Select Files",
    accept_multiple_files=True,
    label_visibility="visible",
    help="Drag and drop files here or click to browse."
)

# Process files automatically when files are uploaded
if uploaded_files:
    with st.spinner("Processing files..."):
        try:
            result = process_files(uploaded_files, compression_level, threads, decompress)
            st.success("Files processed successfully!")
            st.session_state["files_ready"] = True
        except Exception as e:
            st.error(f"Error during processing: {e}")

# Update the download button placeholder based on state
if st.session_state.get("files_ready", False):
    try:
        download_data = get_download_data()
        download_placeholder.download_button(
            label="Download All Files",
            data=download_data,
            file_name="compressed_files.tar.gz",
            mime="application/gzip",
            key="active_download_button"
        )
        # Trigger cleanup after download
        cleanup_response = requests.get(f"{API_BASE_URL}/cleanup")
        if cleanup_response.status_code == 200:
            st.session_state["files_ready"] = False
    except Exception as e:
        download_placeholder.error(f"Error during download: {e}")
else:
    download_placeholder.download_button(
        label="Download All Files",
        data=b"",
        file_name="",
        mime="application/gzip",
        disabled=True,
        key="disabled_download_button"
    )