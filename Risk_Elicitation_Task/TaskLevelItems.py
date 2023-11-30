import numpy as np
from itertools import product
import decimal


ctx = decimal.getcontext()
ctx.rounding = decimal.ROUND_HALF_UP

def flt_key(x:float):
    return round(decimal.Decimal(x), 2)

def fk_tup(*args):
    keys = [flt_key(x) for x in args]
    return tuple(keys)


class TaskLevelItems():
    
    def __init__(self, payouts, r_levels, actions, questions, means):
        """
        Given payouts and levels of risk, calculate the utilities and likelihoods.
        Parameters
        ----------
        payouts : dict
            A dictionary detailing the payouts of this task.  Expecting keys:
                sh - Safe High payout.
                sl - Safe Low payout.
                rh - Risky High payout.
                rl - Risky Low payout.
        r_levels : array-like
            An array-like of risk tolerence parameters.

        Returns
        -------
        None.

        """
        self.payouts = payouts
        
        # Param Space
        self.r_levels = r_levels
        self.actions = actions
        self.questions = questions
        self.means = means
        
        
        
        # Calculate utilities
        self.sh_utilities = {flt_key(r): self.utility(payouts['sh'], r) for r in r_levels}
        self.sl_utilities = {flt_key(r): self.utility(payouts['sl'], r) for r in r_levels}
        self.rh_utilities = {flt_key(r): self.utility(payouts['rh'], r) for r in r_levels}
        self.rl_utilities = {flt_key(r): self.utility(payouts['rl'], r) for r in r_levels}
        
        # Front load the likelihoods
        self.likelihoods = {fk_tup(a, q, r, mu): self.compute_likelihood(a, q, r, mu) for a, q, r, mu in product(actions, questions, r_levels, means)}
        

    @staticmethod
    def utility(payout: float, r: float):
        """
        utility function
        payout: payoff
        r: risk aversion
        """
        utility = (payout ** (1 - r)) / (1 - r)
        return utility


    def compute_likelihood(self, a: int, q: float, r:float, mu:float):
        """
        Likelihood function, probability of answering a (risky = 0, safe = 1)
        a: response (action)
        q: question, probability of high payoff
        r: risk aversion prior
        mu: responsiveness to choice
        """
        
        if a not in [0,1]:
            raise ValueError(f"given a={a}.  Expecting a in {0,1}")
        r_key = flt_key(r)
        
        u_s_hi = self.sh_utilities[r_key]
        u_s_lo = self.sl_utilities[r_key]
        u_r_hi = self.rh_utilities[r_key]
        u_r_lo = self.rl_utilities[r_key]

        likelihood = 1 / (1 + np.exp(-mu * (u_s_hi * q + u_s_lo * (1 - q) - u_r_hi * q - u_r_lo * (1 - q))))
        
        if a == 0:
            return 1 - likelihood
        elif a == 1:
            return likelihood
        
            
    def get_likelihood(self, a: int, q: float, r:float, mu:float):
        """
        Fetches the likelihood
        a: response (action)
        q: question, probability of high payoff
        r: risk aversion prior
        mu: responsiveness to choice
        """
        return self.likelihoods[fk_tup(a,q,r,mu)]

    
    def __str__(self):
        a = []
        a.append(f"Length r: {len(self.r_levels)}")
        a.append(f"Length mu: {len(self.means)}")
        a.append(f"Length questions: {len(self.questions)}")
        a.append(f"Payouts: {self.payouts}")
        a.append(f"Length sh_u: {len(self.sh_utilities)}")
        a.append(f"Length Likelihoods: {len(self.likelihoods)}")
        return "\n".join(a)


class BaseParamSpace():
    R = np.arange(-1, 1, 0.05)
    MU = np.arange(0, 2, 0.1)
    QUESTIONS = np.arange(0, 1.01, .01)
    ACTIONS = [0, 1]
    
    # Calculations based solely on the param space above
    pr = 1 / len(R)
    pmu = 1 / len(MU)
    
    # initial uniform prior
    UNI_PRIOR = np.full((len(R), len(MU)), pr * pmu)
    
    # Initialize the models array
    M_values = np.empty((len(R), len(MU)), dtype=object)
    for i in range(len(R)):
        for j in range(len(MU)):
            M_values[i, j] = (R[i], MU[j])
            

def current_milli_time():
    return round(time.time() * 1000)

if __name__ == '__main__':
    
    import time
    
    PAYOUTS = dict(SH=10, SL=8, RH=19.25, RL=0.50)   
    b = BaseParamSpace()
    
    a = current_milli_time()
    tli = TaskLevelItems(PAYOUTS, b.R, b.ACTIONS, b.QUESTIONS, b.MU)
    b = current_milli_time()
    print(tli)
    print(f"Time (ms): {b-a}")
    
   

    