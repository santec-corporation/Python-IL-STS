"""
Python IL STS process.

@organization: Santec Holdings Corp.
"""


from .drivers import load_dlls

# Get and initialize the logger
from .logger import get_logger
logger = get_logger(__name__)

try:
    # Initialize and Load the Santec DLLs
    setup_dlls_result = load_dlls()
    logger.info("Santec DLLs loaded successfully.")
except Exception as e:
    logger.error("Error while Santec DLLs: ", str(e))
    raise


# Import santec modules
from .connections.get_address import GetAddress
from .measurements.sts_process import StsProcess
from .instruments.daq_device_class import SpuDevice
from .instruments.tsl_instrument_class import TslInstrument
from .instruments.mpm_instrument_class import MpmInstrument
from .utils import file_saving


__all__ = [
    "StsProcess",
    "TslInstrument",
    "MpmInstrument",
    "SpuDevice",
    "GetAddress",
    "file_saving"
]
