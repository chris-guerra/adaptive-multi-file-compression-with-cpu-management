from fastapi import FastAPI, HTTPException, Query
import os
from app import utils, models

app = FastAPI(title="GZIP Compressor API", description="Compress and decompress files using pigz with parallell processing and multiple cores.", version="1.0")

@app.post("/compress/file", response_model=models.OperationResponse)
def compress_file(
    file_path: str = Query(..., description="Path to the single file to compress"),
    compression_level: int = Query(6, ge=1, le=9, description="Compression level (1-9, default 6)"),
    threads: int = Query(8, description="Number of threads to use (default 8 or os.cpu_count() if not provided)"),
    output_path: str = Query(..., description="Directory to save the compressed file"),
    cleanup: bool = Query(False, description="Clean up the original file after compression (default False)")
):
    # Validate that the file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
         raise HTTPException(status_code=400, detail="File path must be an existing file")
    
    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)
    # Construct the output file name using the slugified filename plus .gz
    output_file = os.path.join(output_path, utils.slugify_filename(os.path.basename(file_path)) + ".gz")
    
    result = utils.compress_with_pigz(file_path, output_file, compression_level, threads)
    
    if cleanup and result.get("success"):
         os.remove(file_path)
    
    if not result.get("success"):
         raise HTTPException(status_code=500, detail=result.get("error"))
    
    return models.OperationResponse(
        file_path=output_file,
        original_size=result.get("original_size", 0),
        compressed_size=result.get("compressed_size", 0),
        status="success"
    )

@app.post("/compress/folder", response_model=models.FolderOperationResponse)
def compress_folder(
    input_path: str = Query(..., description="Path to the folder containing files to compress"),
    compression_level: int = Query(6, ge=1, le=9, description="Compression level (1-9, default 6)"),
    threads: int = Query(8, description="Number of threads to use (default 8 or os.cpu_count() if not provided)"),
    output_path: str = Query(..., description="Directory to save the compressed files"),
    cleanup: bool = Query(False, description="Clean up original files after compression (default False)")
):
    # Validate that the input_path exists and is a directory
    if not os.path.exists(input_path) or not os.path.isdir(input_path):
         raise HTTPException(status_code=400, detail="Input path must be an existing directory")
    
    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    responses = []
    # Iterate over each entry in the input_path directory
    for entry in os.listdir(input_path):
         # Skip unwanted files such as .DS_Store
         if entry.lower() == ".ds_store":
              continue
         
         file_path = os.path.join(input_path, entry)
         if os.path.isfile(file_path):
              # Construct the output file name using the slugified filename plus .gz
              output_file = os.path.join(output_path, utils.slugify_filename(entry) + ".gz")
              result = utils.compress_with_pigz(file_path, output_file, compression_level, threads)
              
              responses.append(models.OperationResponse(
                        file_path=output_file,
                        original_size=result.get("original_size", 0),
                        compressed_size=result.get("compressed_size", 0),
                        status="success" if result.get("success") else "failed"
              ))
              
              if cleanup and result.get("success"):
                   os.remove(file_path)
    
    return models.FolderOperationResponse(files=responses)

@app.post("/decompress", response_model=models.OperationResponse)
def decompress_file(
    file: str = Query(..., description="Path to the compressed (.gz) file"),
    output_path: str = Query(..., description="Directory to save the decompressed file"),
    cleanup: bool = Query(True, description="Clean up the compressed file after decompression (default True)")
):
    # Validate that the file exists
    if not os.path.exists(file) or not os.path.isfile(file):
         raise HTTPException(status_code=400, detail="File path must be an existing file")
    
    os.makedirs(output_path, exist_ok=True)
    # Remove the .gz extension for decompression output
    output_file = os.path.join(output_path, os.path.splitext(os.path.basename(file))[0])
    
    result = utils.decompress_with_pigz(file, output_file)
    
    if cleanup and result.get("success"):
         os.remove(file)
    
    if not result.get("success"):
         raise HTTPException(status_code=500, detail=result.get("error"))
    
    return models.OperationResponse(
        file_path=output_file,
        original_size=result.get("original_size", 0),
        compressed_size=result.get("compressed_size", 0),
        status="success"
    )