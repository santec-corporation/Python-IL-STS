"""
Python IL STS process.
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
from .connections.get_instruments import GetInstruments
from .measurements.sts_process import StsProcess
from .instruments.daq_instrument import DaqInstrument
from .instruments.tsl_instrument import TslInstrument
from .instruments.mpm_instrument import MpmInstrument
from .utils import file_saving


__all__ = [
    "StsProcess",
    "TslInstrument",
    "MpmInstrument",
    "DaqInstrument",
    "GetInstruments",
    "file_saving"
]
