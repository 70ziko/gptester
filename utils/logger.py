import datetime
import os

class Logger:
    def __init__(self, path = os.path.join(os.path.dirname(__file__), 'contailligence.log')):
        self.path = path
        self.file = open(path, "a+")

    def log(self, message='', description=''):
        message_to_write = f"[{datetime.datetime.now()}] {description.upper()}\n{message}\n\n\n"
        self.file.write(message_to_write)
