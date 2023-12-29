#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 16:48:51 2023

@author: rossspoon
"""
import jsonpickle
import numpy as np
import sys
import time

if '..' not in sys.path:
    sys.path.append('..')

from common.BinTree import Node

#read in and pickle the decision tree for the risk elicitation task
with open("../common/decision_trees_and_gambles.json", "r") as dec_tree:
    js = dec_tree.read()
DECISION_TREES = jsonpickle.decode(js)


with open("all_dec_trees_12_1.txt", 'w') as outfile:
    for d in DECISION_TREES:
        outfile.write("""====================================================
Risk Lo: {d['rl']} 
Risk Hi: {d['rh']} 
Safe Lo: {d['sl']} 
Safe Hi: {d['sh']}

-- (Down is the SAFE pick) ---
""")
            
        outfile.write(str(d['dec_tree']))