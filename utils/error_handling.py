# utils/error_handling.py

import subprocess
import sys


class CodeQLScanError(Exception):
    pass
