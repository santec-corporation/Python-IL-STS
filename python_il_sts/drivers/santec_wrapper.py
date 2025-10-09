"""
Santec DLLs Wrapper.

- Instrument DLL wrapper.
- STS Process DLL wrapper.
"""


"""
Santec Communication DLL Wrapper.
"""

import Santec.Communication as Comm

# Define the main classes and types for communication
GPIBConnectType = Comm.GPIBConnectType
MainCommunication = Comm.MainCommunication
CommunicationMethod = Comm.CommunicationMethod


"""
Santec Instrument DLL Wrapper.
"""

import Santec

# Santec Communication Terminator and Exception Code Enum classes
CommunicationTerminator = Santec.CommunicationTerminator
ExceptionCode = Santec.ExceptionCode


class TSL(Santec.TSL):
    """Wrapper for the Santec TSL instrument."""

    pass


class MPM(Santec.MPM):
    """Wrapper for the Santec MPM instrument."""

    pass


class DAQ(Santec.SPU):
    """Wrapper for the Santec DAQ (SPU Class) instrument."""

    pass


"""
Santec Connection Enums.
"""

from enum import Enum


class Terminator(Enum):
    """Communication terminators for Santec instruments."""

    CR = CommunicationTerminator.Cr
    LF = CommunicationTerminator.Lf
    CRLF = CommunicationTerminator.CrLf


class GPIBType(Enum):
    """GPIB connection types for Santec instruments."""

    NIVisa = GPIBConnectType.NIVisa
    NI4882 = GPIBConnectType.NI4882
    KeysightVisa = GPIBConnectType.KeysightIO


class ConnectionType(Enum):
    """Connection types for Santec instruments."""

    USB = CommunicationMethod.USB
    GPIB = CommunicationMethod.GPIB
    TCPIP = CommunicationMethod.TCPIP
    DEV = "DAQ"
    NULL = "Unknown"


"""
Santec STS Process DLL Wrapper.
"""

import Santec.STSProcess as Sts

RescalingMode = Sts.RescalingMode
STSDataStruct = Sts.STSDataStruct
STSDataStructForMerge = Sts.STSDataStructForMerge
ModuleType = Sts.Module_Type


class ILSTS(Sts.ILSTS):
    pass


class PDLSTS(Sts.PDLSTS):
    pass