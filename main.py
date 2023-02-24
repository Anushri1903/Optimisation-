#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 11 10:43:47 2022

@author: anushrimore
"""

import multi_machine_solver as mps
import pandas as pd
import os 
       


inputpath = '/Users/anushrimore/Dropbox/Mac/Downloads/optimization_challenge/'
outputpath = '/Users/anushrimore/Dropbox/Mac/Downloads/optimization_challenge/output/'
## Perfo mance matrix 
performance = pd.DataFrame(columns=['machine_id', 'model.ObjVal', 'model.NumVars', 'model.NumConstrs',
  'model.IterCount', 'model.NodeCount', 'model.Runtime'])

number_of_machines = 12

if __name__ == '__main__':
    
    for m_id in range(1,number_of_machines+1):
        vd = mps.Vending_machine(m_id)
        vd.data_preprocessign()
        vl,cl,p=vd.math_model(performance)
        performance=p
        vd.post_procesing(m_id,vl,cl)

# Writting performce matrix
performance.to_csv(os.path.join(outputpath+'performance.csv'))
