"""
Python IL STS - Connection example.
"""

# Import the connection manager class from python_il_sts.
from python_il_sts import ConnectionManager

connect = ConnectionManager()

print(connect.list_instruments())

tsl = connect.connect('TSL-570_22071071_GPIB')
print(tsl.firmware_version)