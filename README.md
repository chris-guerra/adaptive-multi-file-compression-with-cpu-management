# File Compressor API & Frontend

This project provides a FastAPI-based backend and a Streamlit-based frontend for compressing (or decompressing) files using **pigz**. Processed files are stored temporarily and can be downloaded as a single archive.

## Features

- **FastAPI Backend**:
  - Processes multiple file uploads concurrently.
  - Compresses files using pigz (or decompresses if specified).
  - Stores processed files in a temporary directory (`./temp_files`).
  - Provides endpoints to download a single file, download all files (as a tar.gz archive), check status, and cleanup files.

- **Streamlit Frontend**:
  - Drag-and-drop file uploader (main window) with no file size limit.
  - Sidebar options to set compression level, number of threads, and whether to decompress.
  - Automatically starts processing files upon upload.
  - Displays a download button in the sidebar once processing is complete.
  - The "Download All Files" button becomes disabled after files are downloaded and cleaned up.

## Setup and Installation

### Prerequisites

- Python 3.9+
- Install dependencies via pip:
```bash
pip install fastapi uvicorn streamlit requests
```
- pigz must be installed on your system:
- On macOS: `brew install pigz`
- On Ubuntu/Debian: `sudo apt-get install pigz`

#### Running the Backend
	1.	Navigate to the project directory.
	2.	Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

#### Running the Frontend
1.	Navigate to the frontend directory:
```bash
cd frontend
```
2.	Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```
3.	The frontend will open in your browser (usually at http://localhost:8501).

### Usage
1.	Upload Files: Drag and drop files in the main window (or click to browse).
2.	Set Options: Use the sidebar to select compression level, number of threads, and whether to decompress.
3.	Processing: Files are processed automatically once uploaded. A spinner indicates progress.
4.	Download Processed Files: When processing is complete, the sidebar download button becomes enabled.
	- If one file was processed, it will download that file directly.
	- If multiple files were processed, they are archived as tar.gz.
	- After downloading, the backend automatically cleans up the processed files.

License

This project is licensed under the MIT License.

---