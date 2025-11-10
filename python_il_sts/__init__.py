"""
Python IL STS.

Supported Instruments / Devices
    TSL-570 (Any Type)
    MPM-210H & MPM-220
    DAQ (NI USB-6210)

Platform & Requirements
    OS: Windows 10+
    Python: 3.10+
    .NET Framework 4.5.2+
    NI-488.2 for GPIB devices
    NI-VISA for GPIB devices
    NI-DAQmx for DAQ devices
Optional: NI-MAX for configuring/test-running connected devices.
"""

# Import the dll loader function.
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


import sys
if "pydevd" in sys.modules or sys.gettrace():
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend


# Import santec modules
from .connections.get_instruments import GetInstruments
from .connections.connection_manager import ConnectionManager
from .measurements.sts_process import StsProcess
from .instruments.daq_instrument import DaqInstrument
from .instruments.tsl_instrument import TslInstrument
from .instruments.mpm_instrument import MpmInstrument
from .utils import data_utils, plot_utils


__all__ = [
    "GetInstruments",
    "ConnectionManager",
    "TslInstrument",
    "MpmInstrument",
    "DaqInstrument",
    "StsProcess",
    "data_utils",
    "plot_utils"
]
