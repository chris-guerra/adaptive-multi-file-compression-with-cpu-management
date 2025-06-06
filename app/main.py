from fastapi import FastAPI, HTTPException, Query
import os
from app import utils, models

app = FastAPI(
    title="GZIP Compressor API",
    description="Compress and decompress files using pigz with parallel processing and multiple cores.",
    version="1.0"
)

@app.get("/resource-usage")
def get_resource_usage():
    """
    Endpoint to return current resource usage metrics.
    Returns:
      {
         "cpu_percent": <float>,
         "disk_read": <int>,
         "disk_write": <int>
      }
    """
    return utils.log_resource_usage()

@app.post("/compress", response_model=models.FolderOperationResponse)
def compress(
    input_path: str = Query(..., description="Path to the file or folder to compress"),
    compression_level: int = Query(6, ge=1, le=9, description="Compression level (1-9, default 6)"),
    threads: int = Query(None, ge=1, description="Number of threads to use (defaults to maximum available)")
):
    if not os.path.exists(input_path):
        raise HTTPException(status_code=400, detail="Input path must be an existing file or directory")
    
    if threads is None:
        threads = os.cpu_count()
    
    if os.path.isfile(input_path):
        result = utils.compress_file_with_pigz(input_path, compression_level, threads=threads)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        return models.FolderOperationResponse(files=[models.OperationResponse(
            file_path=result.get("compressed_file"),
            original_size=result.get("original_size", 0),
            compressed_size=result.get("compressed_size", 0),
            status="success"
        )])
    elif os.path.isdir(input_path):
        responses = utils.compress_folder_with_pigz(input_path, compression_level, threads=threads)
        for res in responses:
            if not res.get("success"):
                raise HTTPException(status_code=500, detail=f"Compression failed for file {res.get('compressed_file')}: {res.get('error')}")
        return models.FolderOperationResponse(files=[
            models.OperationResponse(
                file_path=res.get("compressed_file"),
                original_size=res.get("original_size", 0),
                compressed_size=res.get("compressed_size", 0),
                status="success"
            ) for res in responses
        ])