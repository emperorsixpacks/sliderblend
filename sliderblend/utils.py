import os

def return_base_dir():
    return os.path.dirname(os.path.dirname(__file__))


BASE_DIR = return_base_dir()
