# python_il_sts/__about__.py

"""
This module contains metadata about the package.
"""

import datetime

# Project name
__project_name__ = "Python-IL-STS"

# Project version
__version__ = "2.10.0-rc1"

# Project metadata
__author__ = "Santec Holdings Corporation"
__license__ = "GNU General Public License v3.0"
__organization__ = "Santec Holdings Corporation"
__description__ = (
    "Python Software for Santec Insertion Loss"
)
__url__ = f"https://github.com/santec-corporation/{__project_name__}"

# Date and copyright
current_year = datetime.date.today().year
__date__ = datetime.date.today().isoformat()
__copyright__ = f"Copyright 2021-{current_year}, {__organization__}"