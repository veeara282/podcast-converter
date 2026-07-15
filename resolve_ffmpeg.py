import logging
import os
from pathlib import Path
import platform
import re

logger = logging.getLogger(__name__)


_REGISTERED_PATHS: set[str] = set()

# Compile this regex once - it matches all the filenames, will be used each time
# _looks_like_ffmpeg_dir() is called
_DLL_PATTERN = re.compile(
    r"(avcodec|avdevice|avfilter|avformat|avutil|swresample|swscale)-.+\.dll$"
)


def _looks_like_ffmpeg_dir(path: str) -> bool:
    """Checks if the given path is a directory that contains known FFmpeg DLL filenames."""
    path_obj = Path(path)
    if not path_obj.is_dir():
        return False
    else:
        logger.debug(f"Found directory: {path}")
        try:
            filenames = [file.name.lower() for file in path_obj.iterdir()]
            logger.debug(f"Files found within directory: {filenames}")
            if any(_DLL_PATTERN.match(fn) for fn in filenames):
                logger.debug("Matching DLLs found.")
                return True
            else:
                logger.debug("No matching DLLs found.")
                return False
        except OSError:
            return False


def add_dll_paths():
    """Adds DLL paths for FFmpeg if this program is running on Windows.
    This is necessary because Python on Windows does not automatically load DLLs from
    the PATH environment variable."""
    if platform.system() == "Windows":
        sys_paths = os.environ.get("PATH", "").split(os.pathsep)
        # Assumes the path matches something like "C:\ffmpeg\bin" (note that Windows
        # file paths are generally case-insensitive)
        paths_to_check = [path for path in sys_paths if "ffmpeg" in path.lower()]
        for path in paths_to_check:
            # If path is already registered, avoid checking it again
            normalized_path = str(Path(path).resolve()).lower()
            if normalized_path not in _REGISTERED_PATHS:
                logger.debug(f"Checking path {path}...")
                if _looks_like_ffmpeg_dir(path):
                    os.add_dll_directory(path)
                    _REGISTERED_PATHS.add(normalized_path)
                    logger.debug(f"Added DLL directory: {path}")
            else:
                logger.debug(f"Path {path} already checked. Skipping.")
