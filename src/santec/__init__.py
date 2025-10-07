"""
Python IL STS process.

@organization: Santec Holdings Corp.
"""

import os
import clr
from .logger import get_logger

logger = get_logger(__name__)

# Add the Santec DLLs to the root.
ROOT = str(os.path.dirname(__file__)) + '\\DLL\\'
logger.info("Getting DLL path, root: %s", ROOT)
# print(ROOT)    # Uncomment in to check if the root was selected properly

DLL1 = 'Santec.Instrument'
DLL2 = 'STSProcess'
result1 = clr.AddReference(ROOT + DLL1)  # Add the Instrument DLL to the root
result2 = clr.AddReference(ROOT + DLL2)  # Add the STSProcess DLL to the root
logger.info("Adding Instrument DLL to the root, result: %s", result1)
logger.info("Adding STSProcess DLL to the root, result: %s", result2)
# print(result1, result2)     # Comment in to check if the DLLs were added.


# Import santec modules
from . import file_saving
from .get_address import GetAddress
from .sts_process import StsProcess
from .daq_device_class import SpuDevice
from .tsl_instrument_class import TslInstrument
from .mpm_instrument_class import MpmInstrument

__all__ = [
    "StsProcess",
    "TslInstrument",
    "MpmInstrument",
    "SpuDevice",
    "GetAddress",
    "file_saving"
]
