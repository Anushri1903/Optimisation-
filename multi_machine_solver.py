#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 10 13:28:57 2022

@author: anushrimore
"""
## Import required python modules 
import gurobipy as gp
import pandas as pd
import numpy as np
from gurobipy import multidict
from gurobipy import GRB
from gurobipy import min_
import os 
from openpyxl import load_workbook
import xlsxwriter


## Input and output data path
inputpath = '/Users/anushrimore/Dropbox/Mac/Downloads/optimization_challenge/'
outputpath = '/Users/anushrimore/Dropbox/Mac/Downloads/optimization_challenge/output/'


class Vending_machine:
       
    def __init__(self,machine_id):
        # Reading the required input files 
        self.machine_id = machine_id
        self.capacity = pd.read_csv(os.path.join(inputpath,'capacity_matrix.csv'))
        self.items = pd.read_csv(os.path.join(inputpath,'items.csv'))
        self.machines= pd.read_csv(os.path.join(inputpath,'machines.csv')) 
        ## Filtering daat for single machine
        self.machines_single = self.machines[self.machines['machine_id']==self.machine_id]
        self.machine_type = self.machines_single['machine_type'].values[0]
        #self.machines_single['machine_type'][0]
        #list(self.machines.loc[self.machines['machine_id']==self.machine_id,'machine_type'].unique())
        #self.columns_shelf=self.capacity.columns
    

        
    def data_preprocessign(self):
        print("function-data_preprocessign")
        
        # Adding column_name feature to the machines 
        self.columns_shelf = [col for col in self.capacity.columns if 'col' in col]
        self.machines_single=self.machines_single.merge(pd.DataFrame(self.columns_shelf), how='cross')
        self.machines_single.rename(columns = {0:'Column'}, inplace = True)
        
        
        ## Data Correction
        correction = {'soda':111 , 'cola':222, 'tropics':333, 'cherry':444,'cola can':555}
        self.machines_single=self.machines_single.replace({"item_id": correction})
    
    
    def math_model(self,performance):
       print("function-math_model")
   
       #Sets-Single machine 
       products = list(self.items['item_id'].unique())
       machine = list(self.machines_single['machine_id'].unique())
       machines_types = list(self.machines_single['machine_type'].unique())
       columns = list(self.columns_shelf)#list(range(1,13)) ## conver to auto
       volumns = list(self.capacity['pack'].unique())
       self.machines_single['item_id'] = self.machines_single['item_id'].apply(pd.to_numeric)
       
       
       #Single machine -Parameters -1
       cap={}
       for j in machines_types: 
           for k in volumns:
               for col in self.columns_shelf:
                   column_name = col #'col'+str(col)
                   cap[j,k,column_name]=self.capacity.loc[(self.capacity['machine_type']==j) & (self.capacity['pack']==k),column_name].values[0]
            

      ## Single Parameters -2
      #𝑠𝑝𝑑𝑚,𝑖,𝑝∈ℝ+ : Supply per day for a machine 𝑚∈𝑀 and type 𝑖∈𝐼 of product 𝑝∈𝑃.
       spdm = {}
       spdm={j:k for j in zip(self.machines_single['machine_id'],self.machines_single['machine_type'],self.machines_single['item_id']) for k in self.machines_single.loc[(self.machines_single['machine_id']==j[0]) & (self.machines_single['machine_type']==j[1]) & (self.machines_single['item_id']==j[2]),'spd']}


      ## Parameters -3
      #𝑣𝑜𝑙𝑝,𝑣∈ℝ+ : Volume of product  𝑝∈𝑃  is  𝑣∈𝑉 .
       volp ={p:v for p in self.items['item_id'] for v in self.items.loc[self.items['item_id']==p,'pack'] }

      
       ## Decision Variable -single machine 
       select1 ={j:0 for j in zip(self.machines_single['machine_id'],self.machines_single['machine_type'],self.machines_single['item_id'],self.machines_single['Column'])}  
       combinations, scores = gp.multidict(select1)
       
       #### Optimisation model
       model = gp.Model('VendingMachineOptimization_singlemachine')
       select_single = model.addVars(combinations, vtype=GRB.BINARY, name='select2')
       
       
       ## Define objective function
       y = model.addVars(products, lb=-GRB.INFINITY, name="y")
       z = model.addVar(vtype=GRB.CONTINUOUS, name="z")
       
       model.addConstrs((y[p] == gp.quicksum(select_single[self.machine_id,self.machine_type,p,c]*cap[self.machine_type,volp[int(p)],c] for c in self.columns_shelf)/spdm[self.machine_id,self.machine_type,p] 
                  for p in products),name="set_y")
       model.addConstr(z == min_(y), name="min constraint")
       model.setObjective(z, sense=GRB.MAXIMIZE)
       
       
       ## constraint-1
       ## Single machine Minimum demand has to be satisfied - Constraint2
       #model.addConstrs((select_single.sum(m,i,p,'*')*cap[i,volp[int(p)],c] >= spdm[m,i,p]
       #for m,i,p,c in select_single.keys()),name="single_min_demand") 
       
       ## Single machine - Constraint2 one column one product constraint 
       model.addConstrs((select_single.sum(m,i,'*',c) <= 1
             for m,i,p,c in select_single.keys()),
            name="single_1_col_1prod") 
       model.optimize()
       
       ## Collecting output 
       ### Post processing output values  
       product_flow = pd.DataFrame(columns=["Machine_id", "Machine_type", "Product","Column","Values","Capacity"])
       for arc in combinations:
          if select_single[arc].x > 1e-6:
              product_flow = product_flow.append({"Machine_id": arc[0], "Machine_type": arc[1],"Product": arc[2], "Column": arc[3],"Values": select_single[arc].x,"Capacity": select_single[arc].x*cap[arc[1],volp[int(arc[2])],arc[3]],"dos":select_single[arc].x*cap[arc[1],volp[int(arc[2])],arc[3]]/spdm[arc[0],arc[1],arc[2]],"spd":spdm[arc[0],arc[1],arc[2]]}, ignore_index=True)  
       product_flow.index=[''] * len(product_flow)
       
       k=product_flow.drop(['Column','Values'], axis=1)
       final_output=k.groupby(['Machine_id','Machine_type','Product','spd']).agg(sum)
       
       
       ## performance matric for each machine 
       performance = performance.append({'machine_id': self.machine_id,
                                        'model.ObjVal':model.ObjVal,
                                        'model.NumVars':model.NumVars,
                                        'model.NumConstrs':model.NumConstrs,
                                        'model.IterCount':model.IterCount,
                                        'model.NodeCount':model.NodeCount,
                                        'model.Runtime':model.Runtime},ignore_index=True)
       
    
    
       return(final_output,product_flow[['Machine_id','Machine_type','Product','Column']],performance)
       
      
        
    def post_procesing(self,machine_id,result1,result2):
        
        with pd.ExcelWriter(os.path.join(outputpath+'machine_id_'+str(machine_id)+'_'+'output.xlsx')) as writer:  
            ## Assignment and arrangement of products to the columns and write excel sheet
            result1.to_excel(writer, sheet_name=str(machine_id)+'assignment')
            result2.to_excel(writer, sheet_name=str(machine_id) +'arragement')
        
        
"""       
performance = pd.DataFrame(columns=['machine_id', 'model.ObjVal', 'model.NumVars', 'model.NumConstrs',
  'model.IterCount', 'model.NodeCount', 'model.Runtime'])
for m_id in range(1,13):
    vd = Vending_machine(m_id)
    vd.data_preprocessign()
    vl,cl,p=vd.math_model(performance)
    performance=p
    vd.post_procesing(m_id,vl,cl)
"""
    