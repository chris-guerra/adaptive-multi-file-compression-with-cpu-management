import os
import tempfile
import subprocess
import re
from fastapi import UploadFile

TEMP_DIR = "./temp_files"

def ensure_temp_dir():
    """Ensure the temporary directory exists."""
    os.makedirs(TEMP_DIR, exist_ok=True)

def save_upload_to_temp(upload_file: UploadFile) -> str:
    """Save the uploaded file to the temporary directory."""
    ensure_temp_dir()
    temp_path = os.path.join(TEMP_DIR, upload_file.filename)
    with open(temp_path, "wb") as f:
        f.write(upload_file.file.read())
    return temp_path

def slugify_filename(filename: str) -> str:
    """
    Slugify the filename: convert to lowercase, replace non-alphanumerics with underscores,
    and preserve the file extension.
    """
    name, ext = os.path.splitext(filename)
    slugified_name = re.sub(r'[^a-zA-Z0-9_]+', '_', name).lower()
    return f"{slugified_name}{ext}"

def get_file_size(file_path: str) -> int:
    """Return the file size in bytes."""
    return os.path.getsize(file_path)

def compress_with_pigz(input_file: str, output_file: str, compression_level: int, threads: int) -> dict:
    """Compress a file using pigz."""
    original_size = get_file_size(input_file)
    try:
        with open(output_file, 'wb') as outfile:
            subprocess.run(
                ["pigz", f"-p{threads}", f"-{compression_level}", "-c", input_file],
                check=True,
                stdout=outfile
            )
        compressed_size = get_file_size(output_file)
        return {"success": True, "original_size": original_size, "compressed_size": compressed_size}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}

def decompress_with_pigz(input_file: str, output_file: str) -> dict:
    """Decompress a file using pigz."""
    try:
        with open(output_file, 'wb') as outfile:
            subprocess.run(
                ["pigz", "-d", "-c", input_file],
                check=True,
                stdout=outfile
            )
        decompressed_size = get_file_size(output_file)
        return {"success": True, "original_size": decompressed_size, "compressed_size": decompressed_size}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}