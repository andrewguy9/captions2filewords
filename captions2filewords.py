import os
from PIL import Image, UnidentifiedImageError

def is_image(filename):
    try:
        with Image.open(filename) as img:
             return True
    except UnidentifiedImageError:
        return False
    return False

def replace_extension(filename, new_extension):
    # Split the filename into root and extension
    root, _ = os.path.splitext(filename)
    # Concatenate root with new extension
    return root + new_extension

def list_file_pairs(directory):
    # Initialize a dictionary to hold file pairs
    file_pairs = {}

    # List all files in the directory
    for file in os.listdir(directory):
        if is_image(os.path.join(directory, file)):
            # Check if the corresponding .txt file exists
            txt_file = replace_extension(file, '.txt')
            if os.path.isfile(os.path.join(directory, txt_file)):
                file_pairs[file] = txt_file
    return file_pairs

def create_caption_dictionary(directory):
    file_pairs = list_file_pairs(directory)
    caption_dict = {}

    for img_file, txt_file in file_pairs.items():
        with open(os.path.join(directory, txt_file), 'r') as file:
            caption = file.read().strip()  # Read and strip any extra whitespace
            caption_dict[img_file] = caption
    return caption_dict

def caption2tags(caption):
    # Split the string by comma
    tags = caption.split(',')

    # Strip whitespace from each tag and filter out empty strings
    cleaned_tags = {tag.strip() for tag in tags if tag.strip()}

    return cleaned_tags

import numpy as np

def tags2tagMatrix(files_and_tags):
    unique_tags = list(set(tag for tags in files_and_tags.values() for tag in tags))
    
    # Create file index
    file_names = list(files_and_tags.keys())
    
    # Initialize a zero matrix
    tag_matrix = np.zeros((len(file_names), len(unique_tags)), dtype=int)
    
    # Populate the matrix
    for row, file in enumerate(file_names):
        for tag in files_and_tags[file]:
            col = unique_tags.index(tag)
            tag_matrix[row, col] = 1
    return tag_matrix, unique_tags, file_names


from sklearn.decomposition import PCA
import numpy as np

def reduceMatrix(tag_matrix, n_components):
    pca = PCA(n_components=n_components)
    pca.fit(tag_matrix)
    reduced_matrix = pca.transform(tag_matrix)
    reversed_matrix = pca.inverse_transform(reduced_matrix)
    loadings = pca.components_

    return reduced_matrix, reversed_matrix, loadings

def loading2Tags(loadings, tags):
    sorted_indices = [np.argsort(-component) for component in loadings]
    ranked_tags = []
    for component_index, indicies in enumerate(sorted_indices):
        ranked_tags.append([tags[index] for index in indicies])
    return ranked_tags

def label_reduced(row, actual_tags, ranked_labels, threshold):
    row_labels = set()
    for idx, value in enumerate(row):
        if value >= threshold:
            matches = [tag for tag in ranked_labels[idx] if tag in actual_tags and tag not in row_labels]
            row_labels.add(matches[0])
    return row_labels

import shutil

def copy_files_to(input_dir, files_and_tags, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    total_images = len(files_and_tags)
    zeroes_needed = len(str(total_images)) + 1
    
    for index, (filename, tags) in enumerate(files_and_tags.items(), start=1):
        num = str(index).zfill(zeroes_needed)
        tag_str = '-'.join(tags)
        ext = os.path.splitext(filename)[1]
        new_filename = f"{num}-{tag_str}{ext}"
        old_path = os.path.join(input_dir, filename)
        new_path = os.path.join(output_dir, new_filename)
        shutil.copy(old_path, new_path)

USAGE="""
Usage:
    captions2filewords [--threshold=<t>] [--num-tags=<n>] [--output=<outdir>] <path>

Options:
    -t --threshold=<t>    Required tag strength [default: 0.5].
    -n --num-tags=<n>     Number of tags to reduce to [default: 5].
    -o --output=<outdir>  Where to place file copies.
    -h --help             Show this screen.

"""

from docopt import docopt

def main(args):
    path = args['<path>']
    threshold = float(args['--threshold'])
    n = int(args['--num-tags'])
    outdir = args['--output']
    captions = create_caption_dictionary(path)
    file2tags = {file: caption2tags(caption) for file, caption in captions.items()}
    tag_matrix, tags, files = tags2tagMatrix(file2tags)
    reduced_matrix, reversed_matrix, loadings = reduceMatrix(tag_matrix, n)
    ranked_labels = loading2Tags(loadings, tags)
    for file, row in zip(file2tags.keys(), reduced_matrix):
        row_labels = label_reduced(row, file2tags[file], ranked_labels, threshold)
        print(file, row_labels)
    if outdir is not None:
        copy_files_to(path, file2tags, outdir)

if __name__ == '__main__':
    arguments = docopt(USAGE)
    main(arguments)
