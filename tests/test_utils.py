import os
import tempfile
import psutil
import mimetypes
from app.utils import log_resource_usage, determine_compression_level, compress_file_with_pigz, get_dynamic_threshold

def test_log_resource_usage():
    """Test that resource usage metrics are logged and returned correctly."""
    usage = log_resource_usage()
    # Ensure keys exist and values are of expected types.
    assert "cpu_percent" in usage
    assert "disk_read" in usage
    assert "disk_write" in usage
    assert isinstance(usage["cpu_percent"], (int, float))
    assert isinstance(usage["disk_read"], int)
    assert isinstance(usage["disk_write"], int)

def test_determine_compression_level_text(tmp_path):
    """For a text file, expect an increased compression level."""
    text_file = tmp_path / "dummy.txt"
    text_file.write_text("This is a sample text." * 100)
    level = determine_compression_level(str(text_file), 6)
    # For text files, we expect a level higher than or equal to 6.
    assert level >= 6

def test_determine_compression_level_image(tmp_path):
    """For an image file, expect a reduced compression level."""
    image_file = tmp_path / "dummy.jpg"
    # Write minimal JPEG header bytes.
    image_file.write_bytes(b"\xff\xd8\xff")
    level = determine_compression_level(str(image_file), 6)
    # For binary image files, expect the level to be less than or equal to 6.
    assert level <= 6

def test_compress_file_with_pigz_resource_usage():
    """Test compressing a file while capturing resource usage metrics."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "testfile.txt")
        with open(file_path, "w") as f:
            f.write("This is a test file for compression. " * 1000)
        result = compress_file_with_pigz(file_path, 6, threads=os.cpu_count())
        # Verify that compression succeeded and that resource usage data is present.
        assert result["success"] is True
        assert "usage_before" in result
        assert "usage_after" in result
        # Ensure the compressed file exists.
        assert os.path.exists(result["compressed_file"])
        # Clean up the compressed file.
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