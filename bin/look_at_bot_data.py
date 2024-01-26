#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 10:13:09 2024

@author: rossspoon
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib_inline

df = pd.read_csv('bot_data/rounds.csv')
df = df[df['session.code'] == '5s0lf9bq']
pv = df.groupby('subsession.round_number')[['group.price', 'group.volume']].max()

pv['group.price'].plot()
#pv['group.volume'].plot(kind='bar')
