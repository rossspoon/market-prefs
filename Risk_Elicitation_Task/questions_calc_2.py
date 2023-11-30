import numpy as np
from itertools import product
from TaskLevelItems import TaskLevelItems, BaseParamSpace, fk_tup, flt_key

import sys
sys.path.append('..')
for p in sys.path:
    print(p)
from common.BinTree import Node

    # pr = 1 / len(R)
    # pmu = 1 / len(MU)
    
    # # initial uniform prior
    # INIT_PRIOR = np.full((len(R), len(MU)), pr * pmu)
    
    # # Initialize the models array
    # M_values = np.empty((len(R), len(MU)), dtype=object)
    # for i in range(len(R)):
    #     for j in range(len(MU)):
    #         M_values[i, j] = (R[i], MU[j])
    
    
#####################################################################################
###
# Everything else depends on the priors, since those change after each choice we need to
# calculate the rest on the fly.
###
#####################################################################################

class KLInfo:
    """Calculate the KL Information for the given set of priors, actions, and questions"""
    def __init__(self, priors, models, tli: TaskLevelItems):
        
        self.tli = tli
        
        actions = tli.actions
        questions = tli.questions
        
        
        self.models = models
        self.priors = priors

        # We can still speed thing up by front loading most of this information
        d0 = models.shape[0]
        d1 = models.shape[1]

        #full_denoms is especially helpful since it can be used in the KL calculations and the prior updations
        self.full_denoms = {(a, flt_key(q)): self.get_denominator_full(a, q) for a, q in product(actions, questions)}
        #print(f"full_denoms: {len(self.full_denoms)}")
        
        #calculate the main denominators
        self.denoms = {(a, flt_key(q), i, j): self.get_denominator(a, q, (i, j)) for a, q, i, j in
                        product(actions, questions, range(d0), range(d1))}
        #print(f"denoms: {len(self.denoms)}")
        
        # Calculate Info numbers
        self.info = {(flt_key(q), i, j): self.get_information_number(q, (i, j)) for q, i, j in
                      product(questions, range(d0), range(d1))}
        #print(f"info: {len(self.info)}")

        
        # Calculate KL
        self.kl = {flt_key(q): self.question_KL(q) for q in questions}
        #print(f"KL: {len(self.kl)}")



    def get_denominator_full(self, a: int, q: float):
        denom = 0
        for i, row in enumerate(self.models):
            for j, element in enumerate(row):
                m = self.models[i, j]
                denom += self.priors[i, j] * self.tli.get_likelihood(a, q, m[0], m[1])
        return denom



    def get_denominator(self, a: int, q: float, k: tuple):
        """
        Get's denominator for get_information_numer function
        Instead of calculating the denominator every time, we can just subtract the prior*likelihood of this
        instance from the pre-calculated self.full_denoms.  (huge time saver)

        a: response (binary)
        q: question, probability of high payoff
        k: specified model
        """
        denom = self.full_denoms[(a, flt_key(q))]
        i, j = k[0], k[1]
        r, mu = self.models[i, j]
        return denom - (self.priors[i, j] * float(self.tli.get_likelihood(a, q, r, mu)))


    def get_information_number(self, q: float, k: tuple):
        """
        Get's denominator for get_information_numer function
        q: question, probability of high payoff
        k: specified model
        """
        I = 0
        i, j = k
        for a in range(2):
            _r, _mu = self.models[k]
            l = float(self.tli.get_likelihood(a, q, _r, _mu))
            d = float(self.denoms[a, flt_key(q), i, j])
            p = self.priors[i, j]
            I += l * np.log( (1 - p) * l / d)
        return 0 if np.isnan(I) else I


    def question_KL(self, q: float):
        """
        Calculates Kullback-Liebler information number for a question
        Q: question, probability of high payoff
        """
        KL = 0
        for i, row in enumerate(self.models):
            for j, element in enumerate(row):
                k = (i, j)
                KL += self.priors[i, j] * self.info[flt_key(q), i, j]
        return KL


    def get_next_Q(self):
        q = max(self.kl, key=self.kl.get)
        inf = self.kl[q]

        return q, inf


    def update_priors(self, a, q):
        """
        Updates the posterior distribution for r and mu
        a: question response
        q: question asked
        """
        updated_p = np.zeros(self.priors.shape)

        denom = self.full_denoms[(a, q)]
        for i, row in enumerate(self.models):
            for j, element in enumerate(row):
                m = self.models[i, j]
                updated_p[i, j] = float(self.tli.get_likelihood(a, q, m[0], m[1])) * self.priors[i, j] / denom
        return updated_p

    
def run_kli(prior, tli, m_vals):
    kli = KLInfo(prior, m_vals, tli)
    q, inf = kli.get_next_Q()
    p1 = kli.update_priors(1, q)
    p0 = kli.update_priors(0, q)

    return q, p1, p0

        
    

   
if __name__ == '__main__':
    import pandas as pd
    ##  Create the Decision tree
    # starting with a uniform prior
    import os
    print(os.getcwd())
    # import json
    import jsonpickle  
    
    gambles = pd.read_csv('gambles.csv')
    num_pay_structs = gambles.shape[0]
    
    ps = BaseParamSpace()
    
    dec_trees = []
    for snum in range(num_pay_structs):
        payouts = gambles.iloc[snum, :]
        print(payouts)
    
        tli = TaskLevelItems(payouts, ps.R, ps.ACTIONS, ps.QUESTIONS, ps.MU)    
    
    
    
        # Build Decision Tree
        node_q = []
        priors_q = []
        
        # initial node
        q, p1, p0 = run_kli(ps.UNI_PRIOR, tli, ps.M_values)
        bin_tree = Node(q)
        node_q.append(bin_tree)
        priors_q.append(p1)
        priors_q.append(p0)
        
        for i in range(7):
            print(i)
            p1 = priors_q.pop(0)
            p0 = priors_q.pop(0)
            q1, pr1, pr0 = run_kli(p1, tli, ps.M_values)
            q0, pl1, pl0 = run_kli(p0, tli, ps.M_values)
        
            node = node_q.pop(0)
            nr = Node(q1)
            nl = Node(q0)
            node_q.append(nr)
            node_q.append(nl)
            node.right = nr
            node.left = nl
        
            priors_q.append(pr1)
            priors_q.append(pr0)
            priors_q.append(pl1)
            priors_q.append(pl0)
        
        
        dec_trees.append(bin_tree)




    #Combine with the gambles data and save to file
    dec_tree_and_gambles = []
    for i in range(len(dec_trees)):
        e = gambles.iloc[i, :].to_dict()
        e['dec_tree'] = dec_trees[i]
        dec_tree_and_gambles.append(e)
        
   # pickle then to JSON
   json_str = jsonpickle.encode(dec_tree_and_gambles)
    print(json_str)
    
    with open("common/decision_trees_and_gambles.json", "w") as out:
        out.write(json_str)

    