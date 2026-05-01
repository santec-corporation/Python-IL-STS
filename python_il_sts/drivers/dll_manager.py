"""
Python-IL-STS DLL Manager.

- Load the Santec DLLs from the default STS application path.
- Load the Santec DLLs from the user AppData path.
"""

import os
import clr
import platform
from pathlib import Path
from ..logger import get_logger

# Get the logger
logger = get_logger(__name__)


class UnsupportedPlatformError(OSError):
    """Raised when Python IL STS is imported on a non-Windows platform."""
    pass


if platform.system() != "Windows":
    error_string = (
        "❌ Python IL STS requires Windows 10/11 with .NET Framework 4.5.2+ installed. "
        f"Current platform: {platform.system()} {platform.release()}"
    )
    logger.error(error_string)
    raise UnsupportedPlatformError(error_string)


# Define the paths for the DLLs
# Default path where the DLLs are expected to be found
SYSTEM_DLL_PATH = r"C:\\Program Files\\santec\\Swept Test System IL And PDL"
APPDATA_DLL_PATH = Path(os.getenv("APPDATA")) / "santec" / "python_il_sts" / "dlls"
FTD2XX_DLL_PATH = r"C:\Windows\System32"

# DLL Names
# List of DLLs to be loaded
DLL_NAMES = ["InstrumentDLL.dll", "STSProcess.dll"]


# Check if DLLs exist
def check_dll_exist(folder_path, dlls: list = None):
    """Checks if the DLLs are present in the provided folder path."""
    dlls = DLL_NAMES if dlls is None else dlls
    return all((Path(folder_path) / dll).exists() for dll in dlls)


def load_dlls():
    """Gets the path where the DLLs exist."""
    if check_dll_exist(SYSTEM_DLL_PATH):
        dll_path = SYSTEM_DLL_PATH
        logger.debug(f"Found DLLs in: {dll_path}")

    elif check_dll_exist(APPDATA_DLL_PATH):
        dll_path = APPDATA_DLL_PATH
        logger.debug(f"Found DLLs in AppData: {dll_path}")
    else:
        raise RuntimeError("DLLs not found.")

    return setup_dlls(dll_path)


def setup_dlls(dll_path, dlls=None):
    """
    Loads the DLLs from the given path.

    :param dll_path: The path from which the dlls have to loaded.
    :param dlls: The list of dlls to be loaded.

    :return: True if all the DLLs were loaded, else False.
    """
    dlls = DLL_NAMES
    for dll in dlls:
        try:
            full_path = os.path.join(dll_path, dll)
            logger.debug(f"Loading DLL: {full_path}")

            # Attempt to load the DLL
            clr.AddReference(full_path)

            logger.debug(f"DLL Loaded: {dll}")

        except Exception as e:
            logger.debug(f"Error loading DLL '{dll}': {e}")
            return False  # Stop on first failure
    return True  # Only returns True if all DLLs are loaded successfully