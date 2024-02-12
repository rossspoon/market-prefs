import numpy as np
import time



# This is an implementation of the DOSE method of risk preference elicitation, as described in:
#         Wang, S.W., Filiba, M. and Camerer, C.F., 2010. Dynamically optimized sequential experimentation (DOSE) 
#         for estimating economic preference parameters. Manuscript submitted for publication.

class BaseParamSpace():
    """
    Collection of parameter values.  These are common to all decision trees, 
    and represent the paramerter space used in the the DOSE calculations.
    """
    R = np.arange(-1.5, 1.55, 0.05)
    MU = np.arange(.1, 6.1, 0.1)
    QUESTIONS = np.arange(0, 1.01, .01)
    ACTIONS = [0, 1]
    
    MODELS = np.empty((len(R), len(MU), 2))
    for i, r in enumerate(R):
        for j, mu in enumerate(MU):
            MODELS[i][j][0] = r
            MODELS[i][j][1] = mu
    
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
    
    def get_r_array(self):
        return self.MODELS[:,:, 0]
    
    def get_mu_array(self):
        return self.MODELS[:, :, 1]
    



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
    
    u_s_hi, u_s_lo, u_r_hi, u_r_lo: the payoffs involved in any H-L payment structure.
    q: question, probability of high payoff
    r: risk aversion prior
    mu: responsiveness to choice
    """
    
    likelihood = 1 / (1 + np.exp(mu * (u_s_hi * q + u_s_lo * (1 - q) - u_r_hi * q - u_r_lo * (1 - q))))
    
    return likelihood


def get_info(likelihood, prior, denom):
    """
    This is the part of equation (3) of the DOSE paper that appear inside the summation.
    Denom is the weighted average of all likelihoods of all R X Mu models, but we
    subtract off the weighted likelihood of each individual model.  This is much
    faster and easier than adding up all but one.

    Parameters
    ----------
    likelihood : np.array
        R X Mu array of likelihoods.
    prior : np.array
        R X Mu array of prior.
    denom : np.array
        The denominator for this calculation.  This should be the weighted sum of the
        likelihoods of all R X MU models.
    Returns
    -------
    TYPE np.array
        R X Mu array of KL info.

    """
    x = ((1-prior) * likelihood ) / (denom-(prior * likelihood))
    # Avoid sending zeros to the log function, replace with nan whiich doesn't seem to trigger a warning from np.log
    x = np.where(x==0, np.nan, x) 
    
    return  fillna((np.log(x) * likelihood))
        
            


def update_prior(likeli, priors, denom:float):
    """
    This is equestion (5) of the DOSE paper.  Updatee the priors based on the action
    that a participant might chose.  The action of the participant is encoded in the
    given likelihoods.

    Parameters
    ----------
    likeli : np.array
        R X MU array of likelihoods.
    priors : np.array
        R X MU array of priors.
    denom : float
        The denominator for this calculation.  This should be the weighted sum of the
        likelihoods of all R X MU models.

    Returns
    -------
    TYPE np.array
        R X Mu of updated priors.

    """
    return likeli * priors / denom
        
            

def current_milli_time():
    """
    Helper to get the current time in milliseconds since the ephoc

    Returns
    -------
    TYPE
        The curren time in milliseconds.

    """
    return round(time.time() * 1000)


def fillna(a:np.array, fill:float=0):
    """
    Helper function to fill the empty elements of an array with the given value (default: 0)

    Parameters
    ----------
    a : np.array
        Array to be filled.
    fill : float, optional
        The fill value. The default is 0.

    Returns
    -------
    a : np.array
        the filled array.

    """
    idx = np.isnan(a)
    a[idx] = fill
    return a
    
    
    
def run_KL(ps:BaseParamSpace, priors, questions, likelihoods):
    """
    Determines the question (probability of the high payout) that maximizes the KL information of the
    given priors and likelihoods.  This an implementation of:
        Wang, S.W., Filiba, M. and Camerer, C.F., 2010. Dynamically optimized sequential experimentation (DOSE) 
        for estimating economic preference parameters. Manuscript submitted for publication.

    Parameters
    ----------
    ps : BaseParamSpace
        Parameters common to all decision trees.  Of main interest are R and MU
    priors : np.array
        R X MU array of priors.
    questions : np.array
        All the questions to consider.  Usually an array from 0 to 1 by .01, or some subset.

    likelihoods : np.array
        A list of lielihoods for each question.  Each element of this array will be a R X MU array.

    Returns
    -------
    max_q : float
        The question (prob of high payout) that associated with the highest KL information.
    p0 : TYPE
        The updated priors if the safe option where to be picked.
        Array will by R X MU in shape.

    p1 : np.array
        The update priors if the risky option where to be picked.
        Array will by R X MU in shape.
    new_q : np.array
        List of possible questions with max_q removed.
    new_likes : np.array
        list of possible sets of likelihoods with the one associated with max_q removed.

    """
    max_kl = None
    max_q = None
    max_ls = None
    max_lr = None
    max_ds = None  #Denominator for the safe likelihoods for the max question
    max_dr = None  #Denominator for the risk likelihoods for the max question
    kls = []

    # Determine the KL info for each question
    # Compare that the running maximum
    for q_idx, q in enumerate(questions):
    
        #Get likelihoods (going to be an R X MU array)
        # there are two sets one for the safe choice and one for the risky
        likeli_s = likelihoods[q_idx]
        likeli_r = 1-likeli_s
                
        # Average of likelihoods weighted by the priors
        # (element-wise multiplication of 2 R X MU arrays)
        weighted_s = likeli_s * priors
        weighted_r = likeli_r * priors
        # The sum over all of these likelihoods is in the denominator for the KL-Info number
        denom_s = sum(sum(weighted_s))  # reducing R X MU arrays to floats
        denom_r = sum(sum(weighted_r))
                
        # Get the KL info 
        # this is the section inside the summation of equation (3) of the DOSE paper
        # likeli_x and priors are R X MU
        # denom is a float
        info_s = get_info(likeli_s, priors, denom_s)
        info_r = get_info(likeli_r, priors, denom_r)
        
        # Sum safe and risky action info together completes the KL info
        # equation (3)
        info = info_s + info_r
        
        # This is equation (4).  An average of all the info from (3)
        # weighted by the priors
        # info and priors are both R X MU arrays
        kl = sum(sum(priors * info))
        kls.append(kl)
    
        # Save return values associated the the maximum KL info
        if max_kl is None or kl > max_kl:
            max_kl = kl
            max_q = q
            max_ls = likeli_s
            max_lr = likeli_r
            max_ds = denom_s
            max_dr = denom_r
            max_q_idx = q_idx
            
    # Remove the max question so that is does not get asked again. 
    #(remove the likelihoods that go with it as well)
    new_q = np.concatenate((questions[0:max_q_idx],  questions[max_q_idx+1:]))
    new_likes = [l for i, l in enumerate(likelihoods) if i != max_q_idx]

    # Update priors.
    # This is equation (5) of the DOSE paper
    # If the question max_q is posed to a participant, that person will
    # choose risky or safe.  Update the priors in both cases
    p0 = update_prior(max_ls, priors, max_ds)
    p1 = update_prior(max_lr, priors, max_dr)
        
    
    return max_q, p0, p1, new_q, new_likes



class Node():
    
    def __init__(self, ps:BaseParamSpace, priors, questions, likelihoods, curr_level=1, max_level=4):
        self.ps = ps
        self.priors = priors
        self.questions = questions
        self.likelihoods = likelihoods
        self.right = None
        self.left = None
        
        q, post_0, post_1, new_q, new_l = run_KL(ps, priors, questions, likelihoods)
        
        self.q = q
        self.post_0 = post_0
        self.post_1 = post_1
        self.new_q = new_q
        self.new_l = new_l
        
        #estimate parameters
        r_arr = ps.get_r_array()
        mu_arr = ps.get_mu_array()
        
        
        self.r0 = sum(sum(r_arr * post_0))
        self.mu0 = sum(sum(mu_arr * post_0))
        self.r1 = sum(sum(r_arr * post_1))
        self.mu1 = sum(sum(mu_arr * post_1))
        
        if curr_level < max_level:
            self.left = Node(ps, post_1, new_q, new_l, curr_level=curr_level+1)
            self.right = Node(ps, post_0, new_q, new_l, curr_level=curr_level+1)
            
    
    def is_leaf(self):
        return self.right is None and self.left is None
 


    def to_dict(self):
        right_d = self.right.to_dict() if self.right else None
        left_d = self.left.to_dict() if self.left else None
        
        return dict(q=self.q,
                    r0 = self.r0,
                    r1 = self.r1,
                    mu0 = self.mu0,
                    mu1 = self.mu1,
                    right = right_d,
                    left = left_d,
                    )
    
    
    @staticmethod
    def str_helper(node, tab=0):
        ret = ''
        right = node.right
        left = node.left

        if right:
            ret += node.str_helper(right, tab=tab+1)
        
        if node.is_leaf():
            ret += f"{'      '*(tab+1)}/(r: {node.r0: .2f}  mu: {node.mu0: .2f})\n"
            
        ret += f"{'      '*tab}{node.q: .2f}\n"
        
        if node.is_leaf():
            ret += f"{'      '*(tab+1)}/(r: {node.r1: .2f}  mu: {node.mu1: .2f})\n"
        
        if left:
            ret += node.str_helper(left, tab=tab+1)
            
        return ret

    
    def __str__(self):
        return self.str_helper(self)
    
    


def get_dec_tree(ps:BaseParamSpace, payouts:dict):
    """
    Generate a decicion tree for the given parameter space and payouts

    Parameters
    ----------
    ps : BaseParamSpace
        Parameters common to all decision trees.
    payouts : dict
        Expecting a dict with keys 'sl', 'sh', 'rl', 'rh'. each one of these is
        a payout expressed as a float.

    Returns
    -------
    bin_tree : common.BinTree
        The decision tree.  A binary tree storing at each node the probability of the high payout.

    """
  
    sh_u = [utility(payouts['sh'], r) for r in bps.R]
    sl_u = [utility(payouts['sl'], r) for r in bps.R]
    rh_u = [utility(payouts['rh'], r) for r in bps.R]
    rl_u = [utility(payouts['rl'], r) for r in bps.R]

    #These likelihoods don't change for the entireity of the decision tree
    # Front load them.
    # For each question, generate a R X MU array of likelihoods
    likelis_for_questions = []
    for q in ps.QUESTIONS:
        likeli_s  = np.zeros( (len(ps.R), len(ps.MU),) )
        for i in range(len(ps.R)):
            for j, mu in enumerate(ps.MU):
                likeli_s[i, j] = compute_likelihood(sh_u[i], sl_u[i], rh_u[i], rl_u[i], q, mu)

        likelis_for_questions.append(likeli_s)

    
    # Build Decision Tree
    bin_tree = Node(ps, ps.UNI_PRIOR, ps.QUESTIONS, likelis_for_questions)

    
    return bin_tree





#################################
##       Main Procedure        ##
#################################
if __name__ == '__main__':
    
    import pandas as pd
    import json
    import multiprocessing as mp
    
    
    # Main Process taskk
    def task(inq:mp.Queue, outq:mp.Queue, ps:BaseParamSpace):
        # List on the input queue for tasks
        for payouts in iter(inq.get, 'STOP'):
            #process generate decision tree
            bin_tree = get_dec_tree(ps, payouts)
            payouts['dec_tree'] = bin_tree

            #put on the output queue
            outq.put(payouts)


    
    start = current_milli_time()
    
    #Load the gambles from a file
    gambles = pd.read_csv('gambles.csv')
    num_pay_structs = gambles.shape[0]
    
    # Parameters like R and MU and the uniform prior are all stored here
    bps = BaseParamSpace()
    
    
    # Set up processes
    ctx = mp.get_context('fork')
    iq = ctx.Queue()
    oq = ctx.Queue()
    procs = [ctx.Process(target=task, args=(iq, oq, bps, ), daemon=True) for _ in range(mp.cpu_count())]
    for p in procs: p.start()
    
    # Add tasks to the input queue
    for i in range(num_pay_structs):
        payouts = gambles.iloc[i, :].to_dict()
        payouts['round_number'] = i + 1
        
        iq.put(payouts)
        
    # Send Termination sigal to Processes
    for _ in procs:
        iq.put('STOP')
        
    # collect results
    print('.' * num_pay_structs)
    dec_trees = []
    for _ in range(num_pay_structs):
        dec_trees.append(oq.get())
        print('.', end='')
    print("\n")
        
    # Wait for processes to terminate
    for p in procs: p.join()
        
    #sort the decision trees by the round number
    dec_trees = sorted(dec_trees, key=lambda x: x['round_number'])
        
    #pickle them to JSON
    json_str = json.dumps(dec_trees, default=lambda o: o.to_dict())     
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
            dec_tree = d['dec_tree']
            outfile.write(str(dec_tree))

    end = current_milli_time()
    print(f"Total Time: {end - start}")
    

## Test Harness.  Use this to test the calculation without the multiprocessing 
## getting in the way.
if __name__ == '__main__2':

    bps = BaseParamSpace()
    #bps.MU = np.arange(0, 10.1, 0.1)

    start = current_milli_time()
    sh_u = [utility(19.25, r) for r in bps.R]
    sl_u = [utility(.5, r) for r in bps.R]
    rh_u = [utility(10, r) for r in bps.R]
    rl_u = [utility(8, r) for r in bps.R]
    likelis_for_questions = []
    for q in bps.QUESTIONS:
        likeli_s  = np.zeros( (len(bps.R), len(bps.MU),) )
        for i in range(len(bps.R)):
            for j, mu in enumerate(bps.MU):
                likeli_s[i, j] = compute_likelihood(sh_u[i], sl_u[i], rh_u[i], rl_u[i], q, mu)

        likelis_for_questions.append(likeli_s)
    t1 = current_milli_time()
    print(f"Likelihoods: {t1-start}")

   
    p = np.ones((len(bps.R), len(bps.MU)))
    s = sum(sum(p))
    prior = p/s
    bps.UNI_PRIOR = prior
    
    q, p1, p0, new_q, new_l = run_KL(bps, prior, bps.QUESTIONS, likelis_for_questions)

    t2 = current_milli_time()
    print(f"KL: {t2-start}")
    print(f"KL: {t2-t1}")
    print(f"Q: {q: .2f}")
    
    a = get_dec_tree(bps, {'sh':10, 'sl': 8, 'rh':19.25, 'rl':0.50})
    print(a)
    
    
    

    