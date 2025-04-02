import os
import tempfile
import psutil
import mimetypes
import pytest
from app.utils import log_resource_usage, determine_compression_level, adjust_threads_for_file, compress_file_with_pigz, get_dynamic_threshold

# Test for enhanced resource monitoring
def test_log_resource_usage():
    usage = log_resource_usage()
    assert "cpu_percent" in usage
    assert "disk_read" in usage
    assert "disk_write" in usage
    assert isinstance(usage["cpu_percent"], (int, float))
    assert isinstance(usage["disk_read"], int)
    assert isinstance(usage["disk_write"], int)

# Test advanced file type detection using python-magic (if available) or mimetypes fallback.
def test_determine_compression_level_text(tmp_path):
    text_file = tmp_path / "dummy.txt"
    text_file.write_text("This is a sample text." * 100)
    level = determine_compression_level(str(text_file), 6)
    # For text files, we expect an increased compression level (i.e. at least 6, possibly higher).
    assert level >= 6

def test_determine_compression_level_image(tmp_path):
    image_file = tmp_path / "dummy.jpg"
    # Write minimal JPEG header bytes.
    image_file.write_bytes(b"\xff\xd8\xff")
    level = determine_compression_level(str(image_file), 6)
    # For image files, we expect the level to be lower than or equal to 6.
    assert level <= 6

# Test dynamic thread allocation based on real-time system load.
def test_adjust_threads_for_file():
    total_cpus = os.cpu_count()
    # Assume 4 files for this test.
    threads = adjust_threads_for_file(total_cpus, 4)
    assert threads >= 1
    # The allocated threads should not exceed total_cpus.
    assert threads <= total_cpus

# Test compress_file_with_pigz resource monitoring and file type-specific adjustments.
def test_compress_file_with_pigz_resource_usage():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "testfile.txt")
        with open(file_path, "w") as f:
            f.write("This is a test file for compression. " * 1000)
        result = compress_file_with_pigz(file_path, 6, threads=os.cpu_count())
        assert result["success"] is True
        assert "usage_before" in result
        assert "usage_after" in result
        assert os.path.exists(result["compressed_file"])
        os.remove(result["compressed_file"])

def test_dynamic_threshold_adjustment():
    # Mock psutil.virtual_memory to simulate low available memory.
    class FakeMem:
        available = 1 * 1024**3  # 1 GB available
    
    original_virtual_memory = psutil.virtual_memory
    psutil.virtual_memory = lambda: FakeMem()
    
    threshold = get_dynamic_threshold()
    # Expect the threshold to drop to 50 MB in low memory conditions.
    assert threshold == 50 * 1024 * 1024
    
    # Restore the original function.
    psutil.virtual_memory = original_virtual_memory