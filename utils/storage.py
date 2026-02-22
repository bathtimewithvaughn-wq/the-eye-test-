"""
Storage utilities
"""

import shutil
from pathlib import Path


def check_disk_space(path: str, required_gb: float = 2.0) -> tuple[bool, float]:
    """
    Check if there's enough disk space for video processing.
    
    Args:
        path: Path to check (uses parent directory if file)
        required_gb: Required space in GB
        
    Returns:
        (has_space, available_gb)
    """
    try:
        p = Path(path)
        if p.is_file():
            p = p.parent
        
        usage = shutil.disk_usage(p)
        available_gb = usage.free / (1024 ** 3)
        
        return available_gb >= required_gb, available_gb
    except Exception as e:
        print(f"Error checking disk space: {e}")
        return True, 0  # Assume OK if check fails


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
