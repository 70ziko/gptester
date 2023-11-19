import datetime
import os

class IOlog:
    COLOR_CODES = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
        "bright_black": "90",
        "bright_red": "91",
        "bright_green": "92",
        "bright_yellow": "93",
        "bright_blue": "94",
        "bright_magenta": "95",
        "bright_cyan": "96",
        "bright_white": "97"
    }

    def __init__(self, verbose=False, name="test"):
        # self.directory = directory
        self.verbose = verbose
        self.log_file = f"{name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_raport.md"
        
        # Ensure the log directory exists
        # os.makedirs(self.log_file, exist_ok=True)
        os.makedirs("raports", exist_ok=True)
        self.log_file = os.path.join('raports', self.log_file)

        with open(self.log_file, 'w') as file:
            file.write('#GPTESTER RAPORT\n')

    def log(self, message, color=None, verbose_only=False):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"{timestamp}: {message}"

        # Append to log file
        with open(self.log_file, 'a') as file:
            file.write(formatted_message + '\n')

        # Check if output is for verbose mode only
        if verbose_only and not self.verbose:
            return

        # Output to console with color
        color_code = self.COLOR_CODES.get(color)
        if color_code:
            print(f"\033[{color_code}m{formatted_message}\033[0m")
        else:
            print(formatted_message)
