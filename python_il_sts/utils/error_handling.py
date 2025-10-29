"""
Error Handling Class.
"""


class InstrumentError(Exception):
    """Custom exception for Instrument errors."""
    pass


class STSProcessError(Exception):
    """Custom exception for STS Process errors."""
    pass


def instrument_error_strings(error_code):
    """
    Instrument error strings.

    Parameters:
        error_code (int): Passed by DLL.

    Returns
        str: InstrumentDLL Error string.

    Raises:
        InstrumentError: If the error code is not recognized.
    """
    instrument_error = {
        -2147483648: "Unknown",
        -40: "InUseError",
        -30: "ParameterError",
        -20: "DeviceError",
        -14: "CommunicationFailure",
        -13: "UnauthorizedAccess",
        -12: "IOException",
        -11: "NotConnected",
        -10: "Uninitialized",
        -2: "TimeOut",
        -1: "Failure",
        -5: "CountMismatch",
        0: "Success",
        11: "AlreadyConnected",
        10: "Stopped"
    }

    error_code = int(error_code)
    if error_code in instrument_error:
        return str(instrument_error[error_code])

    raise InstrumentError(f"Unrecognized error code: {error_code}")


def sts_process_error_strings(error_code):
    """
    STS Process error strings.

    Parameters:
        error_code (int): Passed by DLL.

    Returns:
        str: STSProcess DLL Error string.

    Raises:
        STSProcessError: If the error code is not recognized.
    """
    process_error = {
        -2147483648: "Unknown",
        -1115: "MeasureNotMatch",
        -1114: "MeasureNotRescaling",
        -1113: "MeasureNotExist",
        -1112: "ReferenceNotMatch",
        -1111: "ReferenceNotRescaling",
        -1110: "ReferenceNotExist",
        -1000: "NoCalculated",
        -30: "ParameterError",
        -1: "Failure",
        0: "Success"
    }

    error_code = int(error_code)
    if error_code in process_error:
        return str(process_error[error_code])

    raise STSProcessError(f"Unrecognized error code: {error_code}")
