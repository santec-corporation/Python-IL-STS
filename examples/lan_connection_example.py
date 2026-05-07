"""
Python IL STS - LAN Connection example.
"""

# Import the connection manager class from python_il_sts.
from python_il_sts import ConnectionManager

connect = ConnectionManager()

tsl = connect.connect_tsl('TCPIP0::192.168.1.101::5000::SOCKET')       # TCPIP0::192.168.10.101::5000::SOCKET
print(tsl.firmware_version)