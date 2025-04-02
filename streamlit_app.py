import streamlit as st
import requests
import os

API_BASE_URL = "http://localhost:8000"

def compress_file(file_path, compression_level, threads):
    params = {
        "file_path": file_path,
        "compression_level": compression_level,
        "threads": threads,
        "output_path": "./compressed_files"
    }
    response = requests.post(f"{API_BASE_URL}/compress/file", params=params)
    response.raise_for_status()
    return response.json()

def compress_folder(input_path, compression_level, threads):
    params = {
        "input_path": input_path,
        "compression_level": compression_level,
        "threads": threads,
        "output_path": input_path
    }
    response = requests.post(f"{API_BASE_URL}/compress/folder", params=params)
    response.raise_for_status()
    return response.json()

# Sidebar: Options
st.sidebar.title("Options")
compression_level = st.sidebar.slider("Compression Level", 1, 9, 6)
threads = st.sidebar.number_input("Threads", 1, 32, 8)

# Main area
st.title("File Compressor")
input_text = st.text_input(
    label="Enter a file or folder path to compress",
    value="",
    key="file_input",
    placeholder="path/to/file or path/to/folder"
)

if st.button("Compress"):
    if input_text:
        with st.spinner("Processing..."):
            try:
                # Check if the input is a file or a folder
                if os.path.isfile(input_text):
                    result = compress_file(input_text, compression_level, threads)
                    st.success("File compressed successfully!")
                    st.json(result)
                elif os.path.isdir(input_text):
                    result = compress_folder(input_text, compression_level, threads)
                    st.success("Folder compressed successfully!")
                    st.json(result)
                else:
                    st.error("Invalid path: Please enter a valid file or folder path.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.error("Please enter a valid file or folder path.")