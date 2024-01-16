
import os
from PIL import Image, UnidentifiedImageError

def is_image(filename):
    try:
        with Image.open(filename) as img:
             return True
    except UnidentifiedImageError:
        return False
    return False

def test_file(filename):
    try:
        was_image = is_image(filename)
        if was_image:
            with Image.open(filename) as img:
                 img.load()
            # print("IMAGE", filename)
        else:
            pass
            # print("OTHER", filename)
        
    except Exception as e:
        print("CORRUPT", filename, e)

def apply_function_to_files(root_path, test_function):
    """
    Recursively walk through the directory tree starting at root_path,
    applying test_function to each file.

    :param root_path: The root directory to start the traversal.
    :param test_function: A function that takes a file path as argument and performs some operation.
    """
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            test_function(file_path)

from docopt import docopt
USAGE="""
Usage:
    findbroken <path>

Options:
    -h --help             Show this screen.
"""

def main(args):
    path = args['<path>']
    apply_function_to_files(path, test_file)
    
if __name__ == '__main__':
    arguments = docopt(USAGE)
    main(arguments)
