from fastapi import FastAPI, HTTPException, Query
import os
from app import utils, models

app = FastAPI(
    title="GZIP Compressor API",
    description="Compress and decompress files using pigz with parallel processing and multiple cores.",
    version="1.0"
)

@app.post("/compress", response_model=models.FolderOperationResponse)
def compress(
    input_path: str = Query(..., description="Path to the file or folder to compress"),
    compression_level: int = Query(6, ge=1, le=9, description="Compression level (1-9, default 6)")
):
    if not os.path.exists(input_path):
        raise HTTPException(status_code=400, detail="Input path must be an existing file or directory")
    
    # If input is a file, use compress_file_with_pigz
    if os.path.isfile(input_path):
        result = utils.compress_file_with_pigz(input_path, compression_level, threads=os.cpu_count())
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        return models.FolderOperationResponse(files=[models.OperationResponse(
            file_path=result.get("compressed_file"),
            original_size=result.get("original_size", 0),
            compressed_size=result.get("compressed_size", 0),
            status="success"
        )])
    # If it's a directory, compress folder with automatic decision making
    elif os.path.isdir(input_path):
        responses = utils.compress_folder_with_pigz(input_path, compression_level)
        # If any file failed compression, report error
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