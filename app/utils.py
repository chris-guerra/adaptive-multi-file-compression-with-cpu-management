import os
import subprocess
import concurrent.futures
import psutil
import mimetypes

def log_resource_usage():
    """
    Logs and returns resource usage metrics: CPU percent and disk I/O counters.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    disk_io = psutil.disk_io_counters()
    print(f"CPU Usage: {cpu_percent}%")
    print(f"Disk Read: {disk_io.read_bytes} bytes, Disk Write: {disk_io.write_bytes} bytes")
    return {"cpu_percent": cpu_percent, "disk_read": disk_io.read_bytes, "disk_write": disk_io.write_bytes}

def get_dynamic_threshold(default=100 * 1024 * 1024):
    """
    Returns a dynamic threshold based on available memory and CPU.
    For instance, if available memory is low, lower the threshold.
    """
    mem = psutil.virtual_memory()
    # Example: if available memory is less than 2GB, lower threshold to 50 MB.
    if mem.available < 2 * 1024**3:
        return 50 * 1024 * 1024
    # Otherwise, use the default threshold.
    return default

def determine_compression_level(input_file: str, default_level: int) -> int:
    """
    Adjusts the compression level based on file type.
    - For text files, use a higher compression level.
    - For image/video (binary) files, use a lower level.
    """
    mime_type, _ = mimetypes.guess_type(input_file)
    if mime_type:
        if mime_type.startswith("text"):
            return min(default_level + 2, 9)  # Increase level for text files.
        elif mime_type.startswith("image") or mime_type.startswith("video"):
            return max(default_level - 1, 1)  # Decrease level for binary files.
    return default_level

def compress_file_with_pigz(input_file: str, compression_level: int, threads: int) -> dict:
    """
    Compress a single file using pigz.
    - Uses file type to adjust the compression level.
    - Logs resource usage before and after compression.
    - Writes output to <input_file>.gz, tests integrity with 'pigz -t',
      and attempts to delete the original file.
    Returns a dict with success status, file sizes, the compressed file path,
    and resource usage metrics.
    """
    adjusted_level = determine_compression_level(input_file, compression_level)
    original_size = os.path.getsize(input_file)
    compressed_file = input_file + ".gz"
    
    # Log resource usage before compression
    usage_before = log_resource_usage()
    
    try:
        with open(compressed_file, 'wb') as outfile:
            subprocess.run(
                ["pigz", "-r", "-p", str(threads), f"-{adjusted_level}", "-c", "-f", input_file],
                check=True,
                stdout=outfile
            )
        subprocess.run(
            ["pigz", "-t", compressed_file],
            check=True
        )
        compressed_size = os.path.getsize(compressed_file)
        
        # Log resource usage after compression
        usage_after = log_resource_usage()
        
        # Attempt to delete the original file; if deletion fails, log the error.
        try:
            os.remove(input_file)
        except Exception as cleanup_error:
            print(f"Cleanup failed for {input_file}: {cleanup_error}")
        
        return {
            "success": True,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compressed_file": compressed_file,
            "usage_before": usage_before,
            "usage_after": usage_after
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e), "compressed_file": compressed_file}

def compress_folder_with_pigz(folder_path: str, compression_level: int) -> list:
    """
    Compress all files in a folder recursively.
    Uses the dynamic threshold (from step 1, assumed already added) to decide:
      - If average file size is large, process sequentially with full CPU usage.
      - Otherwise, process in parallel using adjusted thread counts.
    Returns a list of result dictionaries.
    """
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".gz"):
                continue
            file_paths.append(os.path.join(root, file))
    
    num_files = len(file_paths)
    if num_files == 0:
        return []
    elif num_files == 1:
        return [compress_file_with_pigz(file_paths[0], compression_level, threads=os.cpu_count())]
    else:
        total_size = sum(os.path.getsize(fp) for fp in file_paths)
        avg_size = total_size / num_files
        dynamic_threshold = get_dynamic_threshold()
        results = []
        if avg_size > dynamic_threshold:
            for fp in file_paths:
                result = compress_file_with_pigz(fp, compression_level, threads=os.cpu_count())
                results.append(result)
        else:
            total_cpus = os.cpu_count()
            threads_per_file = max(1, total_cpus // num_files)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_file = {executor.submit(compress_file_with_pigz, fp, compression_level, threads_per_file): fp for fp in file_paths}
                for future in concurrent.futures.as_completed(future_to_file):
                    try:
                        result = future.result()
                    except Exception as e:
                        fp = future_to_file[future]
                        result = {"success": False, "error": str(e), "compressed_file": fp + ".gz"}
                    results.append(result)
        return results