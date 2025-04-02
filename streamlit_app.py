import streamlit as st
import requests
import os
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import logging

API_BASE_URL = "http://localhost:8000"

def reinitialize_logging(log_file):
    """Clear existing handlers and reinitialize logging to write to a file."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    root_logger.setLevel(logging.INFO)

def get_resource_usage_from_backend():
    try:
        response = requests.get(f"{API_BASE_URL}/resource-usage")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching resource usage: {e}")
        return None

def format_size(num_bytes):
    if num_bytes < 1024**3:
        return f"{num_bytes / (1024**2):.2f} MB"
    else:
        return f"{num_bytes / (1024**3):.2f} GB"

def shorten_path(full_path):
    return os.path.basename(full_path)

def compress(input_path, compression_level, threads):
    params = {"input_path": input_path, "compression_level": compression_level, "threads": threads}
    response = requests.post(f"{API_BASE_URL}/compress", params=params)
    response.raise_for_status()
    return response.json()

# Reinitialize logging
log_file = "resource_usage.log"
if os.path.exists(log_file):
    os.remove(log_file)
reinitialize_logging(log_file)

st.title("File/Folder Compressor with Resource Monitoring")

input_path = st.text_input("Enter the file or folder path to compress", value="")
compression_level = st.sidebar.slider("Compression Level", 1, 9, 6)
max_threads = os.cpu_count()
threads = st.sidebar.number_input("Threads", min_value=1, max_value=max_threads, value=max_threads, step=1)

log_chart_placeholder = st.empty()
status_placeholder = st.empty()
result_table_placeholder = st.empty()

if st.button("Compress"):
    if not input_path:
        st.error("Please enter a valid file or folder path.")
    else:
        if os.path.exists(log_file):
            os.remove(log_file)
        reinitialize_logging(log_file)
        
        status_placeholder.info("Starting compression...")
        usage_data = []
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(compress, input_path, compression_level, threads)
            while not future.done():
                usage = get_resource_usage_from_backend()
                if usage:
                    usage_data.append(usage)
                    df_usage = pd.DataFrame(usage_data)
                    log_chart_placeholder.line_chart(df_usage[["cpu_percent"]])
                else:
                    log_chart_placeholder.text("Waiting for resource data...")
                time.sleep(1)
            result = future.result()
            final_usage = get_resource_usage_from_backend()
            if final_usage:
                usage_data.append(final_usage)
                df_usage = pd.DataFrame(usage_data)
                log_chart_placeholder.line_chart(df_usage[["cpu_percent"]])
            else:
                log_chart_placeholder.text("No resource data available.")
            
            status_placeholder.success("Compression completed!")
            
            if "files" in result:
                df_result = pd.DataFrame(result["files"])
                if not df_result.empty:
                    df_result["file_path"] = df_result["file_path"].apply(shorten_path)
                    df_result["original_size"] = df_result["original_size"].apply(format_size)
                    df_result["compressed_size"] = df_result["compressed_size"].apply(format_size)
                result_table_placeholder.dataframe(df_result)
            else:
                result_table_placeholder.text("No files were converted.")