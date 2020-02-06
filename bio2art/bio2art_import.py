#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 13:23:00 2020

@author: alexandrosgoulas
"""

#A set of functions for converting biological neuronal networks to artificial
#neuronal networks. The output is a conenctivity matrix (2D numpy array) that 
#can be used in reccurent neuronal networks (e.g., echo state networks).

#Function that simply reads a csv file and returns the matrix that constitutes
#the neuronal network

def bio2art_from_list(path_to_connectome_folder, file):

    #Generate matrix W from scv file
    #
    #input:
    #path_to_connectome_folder: the path to the folder with the csv file
    #file: the name of the csv file
    #
    #output:
    #W: the connectivity matrix in the form of a numpy array
    
    import numpy as np
    import csv
    
    file_to_open = path_to_connectome_folder / file
    
    #Lists to save the name of the neurons
    #It will be needed to convert the csv fiel to an adjacency matrix
    
    #from_list = []
    #to_list = []
    
    all_neuron_names = []
    
    from_indexes_list =[]
    to_indexes_list =[]
    value_connection_list = []
    
    with open(file_to_open, newline='') as f:
        reader = csv.reader(f)
        
        for row in reader:
            
            #Check if the row contains all data
            index = [i for i, list_item in enumerate(row) if list_item == ""]
            
            #If row contains all data, then proceed
            if len(index) == 0:
            
                from_neuron = row[0]  
                to_neuron = row[1]
                
                #strip the strings from spaces so we do not create duplicates
                from_neuron = from_neuron.strip()
                to_neuron = to_neuron.strip()
                
                #Keep track of all the neuron names in the 
                index_from = [i for i, list_item in enumerate(all_neuron_names) if list_item == from_neuron]
                
                if len(index_from) > 0:
                    
                    from_indexes_list.append(index_from[0])
                    
                else:
                    #If it is not in the from neuron list, added and make the index the 
                    #len of list AFTER we add the new name
                    all_neuron_names.append(from_neuron)
                    from_indexes_list.append(len(all_neuron_names)-1)
                  
                #Do the same for the to_neuron     
                index_to = [i for i, list_item in enumerate(all_neuron_names) if list_item == to_neuron]
                
                if len(index_to) > 0:
                    
                    to_indexes_list.append(index_to[0])
                    
                else:
                    #If it is not in the from neuron list, added and make the index the 
                    #len of list AFTER we add the new name
                    all_neuron_names.append(to_neuron)
                    to_indexes_list.append(len(all_neuron_names)-1)    
                    
                
                #Irrespective of the above conditions the value of the connection
                #is stored in its respective list
                value_connection_list.append(float(row[len(row)-2]))
                
    #Build the connectivity matrix
    W = np.zeros((len(all_neuron_names), len(all_neuron_names))) 
    
    for i in range(len(to_indexes_list)-1):
        W[from_indexes_list[i]][to_indexes_list[i]] = value_connection_list[i]
        
    return W        

#Function that constructs a conenctivity matrix C_Neurons with the topology 
#that is dictted by biological neuronal networks.     

def bio2art_from_conn_mat(path_to_connectome_folder, file_conn, ND=None, SeedNeurons=100, intrinsic_conn=True, target_sparsity=0.2, intrinsic_wei=0.8):
    
    #Generate matrix C_Neurons from a biological connectome
    #
    #input:
    #path_to_connectome_folder: the path to the folder with connectome files
    #
    #file: string with the name of the connectome file of the connectome you 
    #would like to use. Currently available:
    #C_Drosophila.npy                 49x49 (shape of the npy array)
    #C_Human_Betzel_Normalized.npy    57x57 
    #C_Macaque_Normalized.npy         29x29
    #C_Marmoset_Normalized.npy        55x55
    #C_Mouse_Gamanut_Normalized.npy   19x19
    #C_Mouse_Ypma_Oh.npy              56x56
    #
    #ND: numpy array of size N where N C.shape[0] with C the actual biological
    #connectome (above). Each entry of ND[i] is denoting the number of neurons 
    #that we assume to inhabit region i. ND by default gets populated with 1s. 
    #Note that each entry of ND is normalized as proportion over the sum(ND)
    #
    #SeedNeurons: Integer denotign the nr of neurons that will be multiplied 
    #by ND[i] to result in the number of neurons to be considered
    #for each region i. Default 100.
    #
    #intrinsic_conn: Boolean denoting if the within regions neuron-to-neuron
    #conenctivity will be generated. Note that currently all-to-all
    #within region conenctions are assumed and implemented.Default True. 
    #
    #target_sparsity: float (0 1] for each source neuron the percentage of all 
    #possible neuron-targets to form connections with. Note that at least 1 
    #neuron will function as target in case that the resultign percentage is<1.
    #This parameter can be used to affect make the sparisty of C_Neurons vary
    #around the density dictated by the actual biological connectomes.
    #Default=0.2. 
    #
    #intrinsic_wei: float (0 1] denoting the percentage of the weight that 
    #will be assigned to the intrinsic weights. E.g., 0.8*sum(extrinsic weight)
    #where sum(extrinsic weight) is the sum of weights of connections from 
    #region A to all other regions, but A.
    #
    #output:
    #C: The actual biological connectome that was used in the form of a numpy 
    #array
    #
    #C_Neurons: the artificial neuronal network in the form of a numpy array
    #
    #Region_Neuron_Ids: A list of list of integers for tracking the neurons of 
    #the C_Neurons array. Region_Neuron_Ids[1] contains a list with integers
    #that denote the neurons of region 1 in C_Neurons as 
    #C_Neurons[Region_Neuron_Ids[1],Region_Neuron_Ids[1]]
    
    
    import numpy as np
    #import csv
    
    file_to_open = path_to_connectome_folder / file_conn
    
    #Read the connectivity matrix - it must be stored as a numpy array
    C = np.load(file_to_open)
    
    #file_to_open = path_to_connectome_folder / file_ND
    
    #ND = np.load(file_to_open)
    
    #What needs to be done is:
    #Use the ND vector to create and connect regions containing neurons that 
    #contain SeedNeurons*ND[i] where ND is the vector specifying the percentage 
    #of neurons for each region i.
    
    if(not(isinstance(ND, np.ndarray))):
        ND=np.ones((C.shape[0],))
        
    
    if(ND.shape[0] != C.shape[0]):
        print("Size of ND must be equal to value of connectome:", C.shape[0])
        return
        
    sum_ND = np.sum(ND)
    ND_scaled_sum = ND / sum_ND
    
    #This is how many neurons each region should have
    Nr_Neurons = np.round(ND_scaled_sum * SeedNeurons)
    
    #Construct the neuron to neuron matrix - it is simply an array of unique
    #integer ids of all the neurons dictated by sum(Nr_Neurons)
    
    all_neurons = np.sum(Nr_Neurons)
    
    index_neurons = [i for i in range(int(all_neurons))]
    index_neurons = np.asarray(index_neurons)
    #index_neurons = index_neurons + 1
    
    #Create a list of lists that tracks the neuron ids that each region 
    #contains
    
    Region_Neuron_Ids=[]
    start = 0
    
    for i in range(C.shape[0]):
        offset = Nr_Neurons[i]
        offset = int(offset)
        
        new_list_of_region = list(range(start, (start + offset)))
        Region_Neuron_Ids.append(new_list_of_region)
        
        #Update the indexes
        start = start + offset
    
    #Rescale the weights so that the outgoing strength of each regions
    #is equal to 1
    sum_C_out = np.sum(C, 0)
    #C_Norm = C / sum_C_out
    
    #Initiate the neuron to neuron connectivity matrix
    C_Neurons = np.zeros((int(all_neurons), int(all_neurons)))
    
    #The not_zeros index marks the regions with which the current region i
    #is connected to. What needs to be done is conencting the respective 
    #neurons constrained in the regions.
    #We use the Region_Neuron_Ids and the weight value of the region-to-region
    #matrix C.
    
    #Start populating by row of the region-to region matrix C
    for i in range(C.shape[0]):
        
        #not-zeros denote the indexes of the areas that are receiving
        #incoming connections from the current region i 
        not_zeros = np.where(C[i,:] > 0)[0]
        #not_zeros = not_zeros[0]
        #Get the neuron source indexes
        sources_indexes = Region_Neuron_Ids[i]
        
        if(intrinsic_conn == True):
            #Add an intrinsic within region weight by interconencting all the 
            #neurons that belong to one region
            
            #Intrinsic weight of within region - default 80%
            intrinsic_weight = (intrinsic_wei * sum_C_out[i]) / (1-intrinsic_wei) 
            
            #Populate the matrix with broadcasting of indexes
            for sources in range(len(sources_indexes)):
                C_Neurons[sources_indexes[sources], sources_indexes] = intrinsic_weight
            
            
        #Loop through the not zeros indexes and fetch the target neuron 
        #Ids that are stored in Region_Neuron_Ids
        for target in range(len(not_zeros)):
            target_indexes = Region_Neuron_Ids[not_zeros[target]]
            
            #Calculate here the strength of connectivity that should be 
            #assigned to the neuron-to-neuron matrix.
            #
            #The weight is dictated by the number of source and target neurons
            #and the respective region-to-region weight of matrix C
            
            current_weight = C[i, not_zeros[target]]
            
            neuron_to_neuron_weight = current_weight / (len(sources_indexes)*len(target_indexes))
            
            #For now the neuron-to-neuron weight is identical due to 
            #lack of the precise number from experimental observations.
            #It migh be needed to inject soem noise for variations to emerge.
            
            #Populate the matrix with broadcasting of indexes
            for sources in range(len(sources_indexes)):
                #C_Neurons[sources_indexes[sources], target_indexes] = neuron_to_neuron_weight
                
                #Here we can control the sparsity of connections by choosing
                #the portion of all target_indexes to be used.
                #Hence, apply the target_sparsity parameter
                nr_targets_to_use = target_sparsity*len(target_indexes)
                
                #Ensure that we keep at least one target neuron
                if nr_targets_to_use < 1:
                    nr_targets_to_use = 1
                else:
                    nr_targets_to_use = int(np.round(nr_targets_to_use))
                
                #Keep random nr_targets_to_use
                target_indexes_to_use = np.random.permutation(len(target_indexes))
                target_indexes_to_use = target_indexes_to_use[0:nr_targets_to_use]
                target_indexes = np.asarray(target_indexes)[target_indexes_to_use]            
                
                C_Neurons[sources_indexes[sources], target_indexes] = neuron_to_neuron_weight
                
            #Remove self-to-self strength/connections
            #Maybe in the future this can be parametrized as a desired 
            #feature to be included or not    
            np.fill_diagonal(C_Neurons, 0.)    
                
    
    return C, C_Neurons, Region_Neuron_Ids