import os
import subprocess
import concurrent.futures
import psutil
import mimetypes
import logging

# Set up logging for resource monitoring
logging.basicConfig(
    filename='resource_usage.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import python-magic for advanced MIME type detection.
try:
    import magic
    USE_MAGIC = True
except ImportError:
    USE_MAGIC = False

def log_resource_usage():
    """
    Logs and returns resource usage metrics: CPU percent and disk I/O counters.
    Also writes metrics to a log file.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    disk_io = psutil.disk_io_counters()
    log_msg = (f"CPU Usage: {cpu_percent}% | "
               f"Disk Read: {disk_io.read_bytes} bytes, Disk Write: {disk_io.write_bytes} bytes")
    print(log_msg)
    logger.info(log_msg)
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
    Uses python-magic if available; otherwise, falls back to mimetypes.
    - For text files, increase compression level (up to 9).
    - For image/video (binary) files, decrease compression level (down to 1).
    """
    mime_type = None
    if USE_MAGIC:
        try:
            # Use magic for a more accurate MIME type detection.
            mime_type = magic.from_file(input_file, mime=True)
        except Exception as e:
            logger.error(f"magic error on file {input_file}: {e}")
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(input_file)
    
    if mime_type:
        if mime_type.startswith("text"):
            return min(default_level + 2, 9)
        elif mime_type.startswith("image") or mime_type.startswith("video"):
            return max(default_level - 1, 1)
    return default_level

def adjust_threads_for_file(total_cpus: int, num_files: int) -> int:
    """
    Dynamically adjusts the number of threads per file based on real-time CPU usage.
    The logic is:
      - If CPU usage is high (>=70%), allocate fewer threads per file.
      - If CPU usage is moderate (40%-70%), allocate a moderate amount.
      - If CPU usage is low (<40%), allocate more threads per file.
    """
    cpu_usage = psutil.cpu_percent(interval=0.5)
    if num_files == 0:
        return total_cpus
    if cpu_usage >= 70:
        threads = max(1, total_cpus // (num_files * 2))
    elif cpu_usage >= 40:
        threads = max(1, total_cpus // (int(num_files * 1.5)))
    else:
        threads = max(1, total_cpus // num_files)
    logger.info(f"Adjusting threads: total_cpus={total_cpus}, num_files={num_files}, cpu_usage={cpu_usage}%, threads_per_file={threads}")
    return threads

def compress_file_with_pigz(input_file: str, compression_level: int, threads: int) -> dict:
    """
    Compress a single file using pigz.
    - Adjusts the compression level based on file type.
    - Logs resource usage before and after compression.
    - Writes output to <input_file>.gz, tests integrity with 'pigz -t',
      and attempts to delete the original file (cleanup errors are logged but do not cause failure).
    Returns a dict with success status, file sizes, the compressed file path, and resource usage metrics.
    """
    adjusted_level = determine_compression_level(input_file, compression_level)
    original_size = os.path.getsize(input_file)
    compressed_file = input_file + ".gz"
    
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
        usage_after = log_resource_usage()
        
        try:
            os.remove(input_file)
        except Exception as cleanup_error:
            logger.error(f"Cleanup failed for {input_file}: {cleanup_error}")
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
        logger.error(f"Compression failed for {input_file}: {e}")
        return {"success": False, "error": str(e), "compressed_file": compressed_file}

def compress_folder_with_pigz(folder_path: str, compression_level: int) -> list:
    """
    Compress all files in a folder recursively.
    Uses dynamic threshold adjustment (assumed to be already implemented) to decide:
      - If average file size is large, process sequentially with full CPU usage.
      - Otherwise, process in parallel using dynamic thread allocation.
    Returns a list of result dictionaries for each file.
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
            # Dynamically adjust threads per file based on current system load.
            threads_per_file = adjust_threads_for_file(total_cpus, num_files)
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

