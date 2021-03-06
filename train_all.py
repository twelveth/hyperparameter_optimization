import os
import random
import time
from itertools import product
import sys

import numpy as np
import torch

from src.train_test import train, test
from src.load_data import load_vectors, prepare_data


def train_all(params_grid, train_data, val_data, test_data, ft_vectors, epochs, device, seed=42):
    rs = random.Random(seed)
    results = []
    start_time = time.time()
    all_params = list(product(*params_grid.values()))
    for i, params in enumerate(all_params):
        trial_start_time = time.time()
        params_dict = {
            'hidden_size': int(params[0]),
            'num_layers': int(params[1]),
            'dropout': 0 if int(params[1]) == 1 else float(params[2]),
            'bidirectional': params[3],
            'batch_size': int(params[4]),
            'lr': params[5],
        }
        print(f'Trials [{i + 1}/{len(all_params)}], {params_dict}')
        if not os.path.isdir('checkpoints'):
            os.mkdir('checkpoints')
        checkpoints_dir = os.path.join('checkpoints', 'models')
        if not os.path.isdir(checkpoints_dir):
            os.mkdir(checkpoints_dir)
        checkpoints_dir = os.path.join(checkpoints_dir, '_'.join(map(str, params)))    
        if not os.path.isdir(checkpoints_dir):
            os.mkdir(checkpoints_dir)
        else:
            print('Already exists, skipping')
            continue
        
        model, fin_val_loss, fin_val_acc = train(params_dict, train_data, val_data, ft_vectors, epochs, device, checkpoints_dir)
        if model is None and fin_val_loss is None and fin_val_acc is None:
            print('Loss is None, bad trial!', end='\n\n')
            continue
        _, test_loss, test_acc = test(model, params_dict['batch_size'], test_data, ft_vectors, device, checkpoints_dir)
        
        time_per_trial = int(time.time() - trial_start_time)
        print(f'Trials [{i + 1}/{len(all_params)}], test loss: {test_loss}, test accuracy: {test_acc}, time per trial: {time_per_trial}s', end='\n\n')
        
        results.append((params, fin_val_loss, fin_val_acc, test_loss, test_acc))
    total_time = int(time.time() - start_time)
        
    return total_time, results


if __name__ == '__main__':
    epochs, device = sys.argv[1:]
    epochs = int(epochs)

    params_grid = {
        'hidden_size': [64, 128, 256, 512],
        'num_layers': np.array([1, 2]),
        'dropout': np.array([0.5]),
        'bidirectional': np.array([True, False]),
        'batch_size': np.array([64, 256]),
        'lr': [1e-3, 1e-2, 1e-1]
    }

    print('Loading fasttext vectors')
    ft_vectors = load_vectors('wiki-news-300d-1M.vec')
    print('Loading IMDB data')
    train_data, val_data, test_data = prepare_data('data/aclImdb/')

    total_time, results = train_all(params_grid, train_data, val_data, test_data, ft_vectors, epochs, device)
    print(f'Total time: {total_time}')

