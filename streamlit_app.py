import streamlit as st
import requests
import os

API_BASE_URL = "http://localhost:8000"

def compress(input_path, compression_level):
    params = {
        "input_path": input_path,
        "compression_level": compression_level
    }
    response = requests.post(f"{API_BASE_URL}/compress", params=params)
    response.raise_for_status()
    return response.json()

st.sidebar.title("Options")
compression_level = st.sidebar.slider("Compression Level", 1, 9, 6)

st.title("File/Folder Compressor")
input_path = st.text_input(
    label="Enter the file or folder path to compress",
    value="",
    placeholder="path/to/file or path/to/folder"
)

if st.button("Compress"):
    if input_path:
        with st.spinner("Processing..."):
            try:
                if os.path.exists(input_path):
                    result = compress(input_path, compression_level)
                    st.success("Compression completed successfully!")
                    st.json(result)
                else:
                    st.error("The specified path does not exist.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.error("Please enter a valid path.")