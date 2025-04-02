# Tar Compressor API

A FastAPI microservice for compressing and decompressing files using pigz. Optimized for multi-threaded compression with the option to clean up original files after compression.

## Features
- Compress single files or entire folders.
- Multi-threaded compression using `pigz`.
- Customizable compression level and thread count.
- Cleanup option to delete original files.
- Health check endpoint.
- Supports both single file and batch folder compression.

---

## Installation

### Prerequisites
- Python 3.9+
- pigz (for multi-threaded compression)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/chris-guerra/tar_compressor
cd tar_compressor
   ```
2.	Set up a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3.	Make sure pigz is installed on your system. On macOS:
```bash
brew install pigz
```
4.	Run the FastAPI application:
```
uvicorn app.main:app --reload
```
5.	Access the API:
```
http://localhost:8000/docs
```

### API Endpoints
	•	GET /health: Health check.
	•	POST /compress/file: Compress a single file.
	•	POST /compress/folder: Compress a folder (tar file).
	•	POST /decompress: Decompress a file.

Refer to the API docs for detailed parameter descriptions.

### Example Usage

```bash
curl -X POST "http://localhost:8000/compress/folder?input_path=/data/in&output_path=/data/out&compression_level=6&threads=8&cleanup=true"
```

License

MIT License

---
