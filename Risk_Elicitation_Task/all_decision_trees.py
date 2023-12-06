import numpy as np
import sys

if '..' not in sys.path:
    sys.path.append('..')
for p in sys.path:
    print(p)
from common.BinTree import Node
import multiprocessing as mp

def utility(payout: float, r: float):
    """
    utility function
    payout: payoff
    r: risk aversion
    """
    return (payout ** (1 - r)) / (1 - r)


def compute_likelihood(u_s_hi, u_s_lo, u_r_hi, u_r_lo, q: float, mu:float):
    """
    Likelihood function, probability of answering a (risky = 0, safe = 1)
    q: question, probability of high payoff
    r: risk aversion prior
    mu: responsiveness to choice
    """
    
    likelihood = 1 / (1 + np.exp(mu * (u_s_hi * q + u_s_lo * (1 - q) - u_r_hi * q - u_r_lo * (1 - q))))
    
    return likelihood


def get_info(likelihood, prior, denom):
    return  np.log( ((1-prior) * likelihood ) / (denom-(prior * likelihood)) ) * likelihood
        
            


class BaseParamSpace():
    R = np.arange(-1, 1.05, 0.05)
    MU = np.arange(0, 4.1, 0.1)
    QUESTIONS = np.arange(0, 1.01, .01)
    ACTIONS = [0, 1]
    
    # Calculations based solely on the param space above
    pr = 1 / len(R)
    pmu = 1 / len(MU)
    
    # initial uniform prior
    UNI_PRIOR = np.full((len(R), len(MU)), pr * pmu)
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        str = ""
        str += f"R: {min(self.R): .2f} - {max(self.R): .2f} \n"
        str += f"MU: {min(self.MU): .2f} - {max(self.MU): .2f} \n"
        str += f"Questions: {min(self.QUESTIONS): .2f} - {max(self.QUESTIONS): .2f} \n"
        str += f"Actions: {self.ACTIONS}"
        return str
            

            

def update_prior(likeli, priors, denom):
    return likeli * priors / denom
        
            

def current_milli_time():
    return round(time.time() * 1000)

def fillna(a:np.array, fill:float=0):
    idx = np.isnan(a)
    a[idx] = fill
    
    
    
def run_KL(ps:BaseParamSpace, priors, questions, sh_u, sl_u, rh_u, rl_u):
    max_kl = -99
    max_q = -99
    max_ls = None
    max_lr = None
    kls = []

    for q_idx, q in enumerate(questions):
    
        likeli_s  = np.zeros( (len(ps.R), len(ps.MU),) )
        for i in range(len(ps.R)):
            for j, mu in enumerate(ps.MU):
                likeli_s[i, j] = compute_likelihood(sh_u[i], sl_u[i], rh_u[i], rl_u[i], q, mu)
                
        
        likeli_r = 1-likeli_s
                
        weighted_s = likeli_s * priors
        weighted_r = likeli_r * priors

        denom_s = sum(sum(weighted_s))
        denom_r = sum(sum(weighted_r))
                
        
        info_s = get_info(likeli_s, priors, denom_s)
        info_r = get_info(likeli_r, priors, denom_r)
        fillna(info_s)
        fillna(info_r)
        
        info = info_s + info_r
        kl = sum(sum(priors * info))
        kls.append(kl)
    
        if kl > max_kl:
            max_kl = kl
            max_q = q
            new_q = np.concatenate((questions[0:q_idx],  questions[q_idx+1:]))
            max_ls = likeli_s
            max_lr = likeli_r
            
    p0 = update_prior(max_ls, priors, denom_s)
    p1 = update_prior(max_lr, priors, denom_r)
        
    
    return max_q, p0, p1, new_q



def get_dec_tree(ps:BaseParamSpace, payouts:dict):
  
    sh_u = [utility(payouts['sh'], r) for r in bps.R]
    sl_u = [utility(payouts['sl'], r) for r in bps.R]
    rh_u = [utility(payouts['rh'], r) for r in bps.R]
    rl_u = [utility(payouts['rl'], r) for r in bps.R]
 
    
    # Build Decision Tree
    node_q = []
    priors_q = []
    questions = []
    
    # initial node
    q, p1, p0, new_q = run_KL(ps, ps.UNI_PRIOR, ps.QUESTIONS, sh_u, sl_u, rh_u, rl_u)
    bin_tree = Node(q)
    node_q.append(bin_tree)
    priors_q.append(p1)
    priors_q.append(p0)
    questions.append(new_q)
    
    for i in range(7):
        p1 = priors_q.pop(0)
        p0 = priors_q.pop(0)
        new_q = questions.pop(0)
        
        q1, pr1, pr0, newq_1 = run_KL(ps, p1, new_q, sh_u, sl_u, rh_u, rl_u)
        q0, pl1, pl0, newq_0 = run_KL(ps, p0, new_q, sh_u, sl_u, rh_u, rl_u)
        
    
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
        questions.append(newq_1)
        questions.append(newq_0)
    
    return bin_tree


def task(inq:mp.Queue, outq:mp.Queue, ps:BaseParamSpace):
    for payouts in iter(inq.get, 'STOP'):
        a = current_milli_time()
        bin_tree = get_dec_tree(ps, payouts)
        payouts['dec_tree'] = bin_tree
        b = current_milli_time()
        print(f"Time: {b-a}")
        outq.put(payouts)


if __name__ == '__main__':
    
    import time
    import pandas as pd
    import jsonpickle
    
    start = current_milli_time()
    
    gambles = pd.read_csv('gambles.csv')
    num_pay_structs = gambles.shape[0]   
    bps = BaseParamSpace()
       
    
    # Set up processes
    ctx = mp.get_context('fork')
    iq = ctx.Queue()
    oq = ctx.Queue()
    procs = [ctx.Process(target=task, args=(iq, oq, bps, ), daemon=True) for _ in range(mp.cpu_count())]
    for p in procs: p.start()
    
    # Add tasks to the input queue
    dec_trees = []
    for i in range(num_pay_structs):
        payouts = gambles.iloc[i, :].to_dict()
        payouts['round_number'] = i + 1
        
        iq.put(payouts)
        
    # Send Termination sigal to Processes
    for _ in range(num_pay_structs):
        iq.put('STOP')
        
    # collect results
    for _ in range(num_pay_structs):
        dec_trees.append(oq.get())
        
    # Wait for processes to terminate
    for p in procs:
        p.join()
        

    #sort the decision trees by the round number
    dec_trees = sorted(dec_trees, key=lambda x: x['round_number'])
        
    # pickle then to JSON
    json_str = jsonpickle.encode(dec_trees)     
    with open("decision_trees_and_gambles.json", "w") as out:
          out.write(json_str)
         
         
    # write in a human-readable way.
    with open("all_dec_trees.txt", 'w') as outfile:
        outfile.write("========================\n")
        outfile.write("=====  PARAM SPACE =====\n")
        outfile.write(str(bps))
        outfile.write("\n========================\n")
        for d in dec_trees:
            outfile.write(f"====================================================\nRound: {d['round_number']}\nRisk Lo: {d['rl']} \nRisk Hi: {d['rh']} \nSafe Lo: {d['sl']} \nSafe Hi: {d['sh']} \n\n-- (Down is the SAFE pick) ---\n")                
            outfile.write(str(d['dec_tree']))

    end = current_milli_time()
    print(f"Total Time: {end - start}")