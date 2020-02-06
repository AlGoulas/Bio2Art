#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 13:31:03 2019

@author: alexandrosgoulas
"""

#Compare memory performance in a lagged sequence memory task of a reservoir 
#with random topology and a reservoir with topology based on a biological 
#neuronal network

#IMPORTANT: ESN are depending on many parameters that can have a tremendous
#impact on the performance (e.g., activation function, weigh values of 
#Win and Wrec matrices, etc). So meaningful comparisons requeire a search
#over parameters. The example here is just to desmontrate use
#of the bio2art and esn, NOT for drawing final conclusions.


#Define some usuful functions for matrix density and a custom sigmoid
#to be optionally used as an activation function.

def density_matrix(X):
    
    import numpy as np
    
    #Calculate the current density of the matrix
    #It included the diagonal!
    X_size = X.shape
    non_zeros = np.where(X != 0)
    
    density = len(non_zeros[0]) / (X_size[0] * X_size[1])
    
    return density



def threshold_matrix(X, desired_density):
    
    import numpy as np
    
    #Calculate the current density of the matrix
    #It included the diagonal!
    X_size = X.shape
    current_non_zeros = np.where(X != 0)
    
    current_density = len(current_non_zeros[0]) / (X_size[0] * X_size[1])
    
    #Clearly the operation makes sense 
    if(current_density <= desired_density):
        
        print("Current density smaller or equal than the desired one...")
        
    else:
        
        desired_non_zeros = desired_density * (X_size[0] * X_size[1])
        
        nr_entries_to_set_to_zero = int(np.round(len(current_non_zeros[0]) - desired_non_zeros)) 
    
        current_non_zeros_rand_index = np.random.permutation(len(current_non_zeros[0]))
        
        x = current_non_zeros[0]
        y = current_non_zeros[1]
        
        x = x[current_non_zeros_rand_index[0:nr_entries_to_set_to_zero]]
        y = y[current_non_zeros_rand_index[0:nr_entries_to_set_to_zero]]
        
        X[(x,y)] = 0
        
    return X
    

#Convert connectome to matrix     
from pathlib import Path

import numpy as np

#Optional specification of inhomogenoous number of neurons. Comment out and 
#tailor accordingly. Otherwise ND=None
#ND_areas = np.random.choice([10, 8, 1], p=[.1, .1, .8], size=(57,))

import bio2art_import as b2a

#Specify here the folder where your connectomes are contained 
path_to_connectome_folder = Path("/Users/alexandrosgoulas/Data/work-stuff/python-code/Bio2Art/connectomes/")

#Specify here the connectome that you would like to use
file_conn = "C_Marmoset_Normalized.npy"

C, C_Neurons, Region_Neuron_Ids = b2a.bio2art_from_conn_mat(
    path_to_connectome_folder, 
    file_conn, 
    ND=None, 
    SeedNeurons=600, 
    intrinsic_conn=True, 
    target_sparsity=0.1
    )

#Keep in this variable the size of the C_Neurons to intiialize the reservoir
size_of_matrix = C_Neurons.shape[0]


#Echo state network memory

from echoes.tasks import MemoryCapacity
from echoes.plotting import plot_forgetting_curve, set_mystyle
set_mystyle() # make nicer plots, can be removed

# Echo state network parameters (after Jaeger)
n_reservoir = size_of_matrix
W = np.random.choice([0, .47, -.47], p=[.8, .1, .1], size=(size_of_matrix, size_of_matrix))
W_in = np.random.choice([.1, -.1], p=[.5, .5], size=(n_reservoir, 2))

spectral_radius = .9

density_for_reservoir = density_matrix(C_Neurons)
W = threshold_matrix(W, density_for_reservoir)

# Task parameters (after Jaeger)
inputs_func=np.random.uniform
inputs_params={"low":-.1, "high":.1, "size":300}
lags = [1, 2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]

#Random reservoir
#Initialize the reservoir object
esn_params = dict(
    n_inputs=1,
    n_outputs=len(lags),  # automatically decided based on lags
    n_reservoir=size_of_matrix,
    W=W,
    W_in=W_in,
    spectral_radius=spectral_radius,
    bias=0,
    n_transient=100,
    regression_params={
        "method": "pinv"
    },
    #random_seed=42,
)

# Initialize the task object
mc = MemoryCapacity(
    inputs_func=inputs_func,
    inputs_params=inputs_params,
    esn_params=esn_params,
    lags=lags
).fit_predict()  # Run the task

#Plot the memory curve for the reservoir with random topology
plot_forgetting_curve(mc.lags, mc.forgetting_curve_)


#What we retouch for the bio2art network is W. To this end, get the unique 
#pair of values that the random reservoir was initialized with and replace
#the actual weights of the C_Neurons

#Get the indexes for the non zero elements of C_Neurons
non_zero_C_Neurons = np.where(C_Neurons != 0)

x_non_zero_C_Neurons = non_zero_C_Neurons[0]
y_non_zero_C_Neurons = non_zero_C_Neurons[1]

rand_indexes_of_non_zeros = np.random.permutation(len(x_non_zero_C_Neurons))

indexes_for_unique1 = int(np.floor(len(rand_indexes_of_non_zeros)/2))

#Assign the same weight as for the random reervoir for a comparison
C_Neurons[(x_non_zero_C_Neurons[rand_indexes_of_non_zeros[0:indexes_for_unique1]], 
            y_non_zero_C_Neurons[rand_indexes_of_non_zeros[0:indexes_for_unique1]])] = .47

C_Neurons[(x_non_zero_C_Neurons[rand_indexes_of_non_zeros[indexes_for_unique1:]], 
            y_non_zero_C_Neurons[rand_indexes_of_non_zeros[indexes_for_unique1:]])] = -.47


#Bio connectome reservoire 
# Initialize the reservoir
esn_params = dict(
    n_inputs=1,
    n_outputs=len(lags),  # automatically decided based on lags
    n_reservoir=size_of_matrix,
    W=C_Neurons,
    W_in=W_in,
    spectral_radius=spectral_radius,
    bias=0,
    n_transient=100,
    regression_params={
        "method": "pinv"
    },
    #random_seed=42,
)

# Initialize the task object 
mc_bio = MemoryCapacity(
    inputs_func=inputs_func,
    inputs_params=inputs_params,
    esn_params=esn_params,
    lags=lags
).fit_predict()  # Run the task

#Plot the memory curve for the reservoir with the biological connectome 
#topology
plot_forgetting_curve(mc_bio.lags, mc_bio.forgetting_curve_)
      