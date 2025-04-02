import os
import subprocess
import shutil
import unicodedata
import re
import tarfile

def slugify_filename(filename: str) -> str:
    """
    Slugify the base name of a filename while preserving its extension.
    Example: "Cool Fíle.csv" -> "cool_file.csv"
    """
    base, ext = os.path.splitext(filename)
    base = unicodedata.normalize('NFKD', base).encode('ascii', 'ignore').decode('ascii')
    base = re.sub(r'[^\w\s-]', '', base).strip().lower()
    base = re.sub(r'[-\s]+', '_', base)
    return f"{base}{ext.lower()}"


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)

def compress_with_pigz(input_file: str, output_file: str, compression_level: int, threads: int) -> dict:
    """
    Compress the file using pigz with the given compression level and threads.
    Returns a dict with success status and file size details.
    """
    original_size = get_file_size(input_file)
    try:
        # Command: pigz -p<threads> -<compression_level> -c <input_file> > <output_file>
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
    """
    Decompress the file using pigz.
    Returns a dict with success status and file size details.
    """
    try:
        # Command: pigz -d -c <input_file> > <output_file>
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

def extract_tar(archive_path: str, extract_path: str) -> bool:
    """
    Extract a tar archive to a given directory.
    Returns True if successful, False otherwise.
    """
    try:
        os.makedirs(extract_path, exist_ok=True)
        with tarfile.open(archive_path, 'r:*') as tar:
            tar.extractall(path=extract_path)
        return True
    except Exception as e:
        print(f"Error extracting tar: {e}")
        return False