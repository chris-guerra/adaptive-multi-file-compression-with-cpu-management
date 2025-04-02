from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
import os
import tarfile
import shutil
from app import utils, models
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(
    title="File Compressor API",
    description="Compress and decompress files using pigz",
    version="1.0"
)

TEMP_DIR = "./temp_files"

@app.get("/health")
def health_check():
    """Simple health check."""
    return {"status": "healthy"}

@app.get("/status")
def status():
    """Return whether there are processed files in TEMP_DIR."""
    files = os.listdir(TEMP_DIR) if os.path.exists(TEMP_DIR) else []
    return {"files_ready": len(files) > 0}

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    """Serve a single processed file for download."""
    file_path = os.path.join(TEMP_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/octet-stream", filename=file_name)
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.get("/download_all")
async def download_all_files():
    """
    Serve all processed files:
      - If only one file exists, serve it directly.
      - If multiple files exist, package them into a tar.gz archive.
    """
    if not os.path.exists(TEMP_DIR):
        return JSONResponse({"error": "No files to download"}, status_code=404)
    files = [f for f in os.listdir(TEMP_DIR) if os.path.isfile(os.path.join(TEMP_DIR, f))]
    if not files:
        return JSONResponse({"error": "No files to download"}, status_code=404)
    if len(files) == 1:
        file_path = os.path.join(TEMP_DIR, files[0])
        return FileResponse(file_path, media_type="application/octet-stream", filename=files[0])
    tar_filename = "all_files.tar.gz"
    tar_path = os.path.join(TEMP_DIR, tar_filename)
    with tarfile.open(tar_path, "w:gz") as tar:
        for file_name in files:
            if file_name != tar_filename:
                tar.add(os.path.join(TEMP_DIR, file_name), arcname=file_name)
    return FileResponse(tar_path, media_type="application/gzip", filename=tar_filename)

@app.get("/cleanup")
async def cleanup_files():
    """Delete all processed files from the temp directory."""
    try:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
        return JSONResponse({"message": "All files deleted"}, status_code=200)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def process_file(temp_path: str, output_file: str, compression_level: int, threads: int, decompress: bool):
    """Helper function to compress or decompress a single file."""
    if decompress:
        result = utils.decompress_with_pigz(temp_path, output_file)
    else:
        result = utils.compress_with_pigz(temp_path, output_file, compression_level, threads)
    utils.ensure_temp_dir()
    final_output = os.path.join(TEMP_DIR, os.path.basename(output_file))
    os.replace(output_file, final_output)
    try:
        os.remove(temp_path)
    except Exception as e:
        result["error"] = f"Failed to delete temporary file: {e}"
    return {
        "file_path": final_output,
        "original_size": result.get("original_size", 0),
        "compressed_size": result.get("compressed_size", 0),
        "status": "success" if result.get("success") else f"failed - {result.get('error', 'unknown error')}"
    }

@app.post("/process/files", response_model=models.MultiFileOperationResponse)
async def process_files(
    files: list[UploadFile] = File(..., description="Upload one or more files for processing"),
    compression_level: int = Query(6, ge=1, le=9, description="Compression level (1-9, default 6)"),
    threads: int = Query(8, description="Number of threads to use (default 8)"),
    decompress: bool = Query(False, description="If true, decompress instead of compress")
):
    """Process multiple files concurrently for compression or decompression."""
    responses = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for file in files:
            temp_path = utils.save_upload_to_temp(file)
            output_filename = utils.slugify_filename(file.filename)
            if decompress:
                output_file = os.path.join(TEMP_DIR, os.path.splitext(output_filename)[0])
            else:
                output_file = os.path.join(TEMP_DIR, f"{output_filename}.gz")
            futures.append(executor.submit(process_file, temp_path, output_file, compression_level, threads, decompress))
        for future in futures:
            result = future.result()
            responses.append(models.OperationResponse(
                file_path=result.get("file_path", ""),
                original_size=result.get("original_size", 0),
                compressed_size=result.get("compressed_size", 0),
                status=result.get("status", "failed")
            ))
    return models.MultiFileOperationResponse(files=responses)