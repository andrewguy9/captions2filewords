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

def rankTagsByLoading(loadings, tags):
    sorted_indices = [np.argsort(-np.abs(component)) for component in loadings]
    
    selected_indices = []
    maximized_sum = 0.0
    
    for component_index, indices in enumerate(sorted_indices):
        for idx in indices:
            if idx not in selected_indices:
                selected_indices.append(idx)
                maximized_sum += abs(loadings[component_index][idx])
                break
    tag_strs = [tags[idx] for idx in selected_indices]
    return tag_strs

def label_reduced(reduced_row, labels, threshold):
    row_labels = []
    for idx, value in enumerate(reduced_row):
        if abs(value) >= threshold:
            row_labels.append(labels[idx])
    return row_labels

USAGE="""
Usage:
    captions2filewords <path>

Options:
    -h --help     Show this screen.

"""

from docopt import docopt

def main(args):
    path = args['<path>']
    captions = create_caption_dictionary(path)
    file2tags = {file: caption2tags(caption) for file, caption in captions.items()}
    tag_matrix, tags, files = tags2tagMatrix(file2tags)
    reduced_matrix, reversed_matrix, loadings = reduceMatrix(tag_matrix, 5)
    reduced_labels = rankTagsByLoading(loadings, tags)
    for file, row in zip(file2tags.keys(), reduced_matrix):
        print(file, label_reduced(row, reduced_labels, .5))

if __name__ == '__main__':
    arguments = docopt(USAGE)
    main(arguments)
