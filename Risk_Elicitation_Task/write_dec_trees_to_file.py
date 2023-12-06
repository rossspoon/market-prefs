#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 16:48:51 2023

@author: rossspoon
"""
import jsonpickle

#read in and pickle the decision tree for the risk elicitation task
with open("../common/decision_trees_and_gambles2.json", "r") as dec_tree:
    js = dec_tree.read()
DECISION_TREES = jsonpickle.decode(js)


with open("../Risk_Elicitation_Task/all_dec_trees.txt", 'w') as outfile:
    for d in DECISION_TREES:
        outfile.write("""====================================================
Risk Lo: {d['rl']} 
Risk Hi: {d['rh']} 
Safe Lo: {d['sl']} 
Safe Hi: {d['sh']}

-- (Down is the SAFE pick) ---
""")
            
        outfile.write(str(d['dec_tree']))