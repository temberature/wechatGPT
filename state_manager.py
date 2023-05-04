from itertools import zip_longest
import json
import time
from collections import Counter

import numpy as np

def save_state(state):
    with open('state.json', 'w') as f:
        json.dump(state, f)

def load_state():
    with open('state.json', 'r') as f:
        return json.load(f)

def update_first_x_coords(coords):
    state = load_state()
    state['first_x_coords'].append(coords)
    state['first_x_coords'] = state['first_x_coords'][-99:] # Keep only the latest 10 items
    print(len(state['first_x_coords']))
    save_state(state)

def update_prob(prob):
    state = load_state()
    state['prob'] = prob
    save_state(state)



def get_most_common_coords():
    state = load_state()
    first_x_coords = state['first_x_coords']
    median_coords = []

    for coords in zip_longest(*first_x_coords, fillvalue=0):
        # Filter out None values and convert to a NumPy array
        filtered_coords = np.array([coord for coord in coords if coord is not None])

        # Calculate the median
        
        median_coord = np.median(filtered_coords)
        median_coords.append(median_coord)

    print("Median coordinates:", median_coords)
    return median_coords



