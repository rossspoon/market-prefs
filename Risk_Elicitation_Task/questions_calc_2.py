import numpy as np
from itertools import product
import decimal

ctx = decimal.getcontext()
ctx.rounding = decimal.ROUND_HALF_UP

R = [round(decimal.Decimal(x), 2) for x in np.arange(-1, 1, 0.05)]
MU = [round(decimal.Decimal(x), 2) for x in np.arange(0, 2, 0.1)]
QUESTIONS = [round(decimal.Decimal(x), 2) for x in np.arange(0, 1.01, .01)]
PAYOUTS = [decimal.Decimal(x) for x in ['10', '8', '19.25', '0.50']]
ACTIONS = [0, 1]

pr = 1 / len(R)
pmu = 1 / len(MU)

# initial uniform prior
P = np.full((len(R), len(MU)), pr * pmu)

# Initialize the models array
M_values = np.empty((len(R), len(MU)), dtype=object)
for i in range(len(R)):
    for j in range(len(MU)):
        M_values[i, j] = (R[i], MU[j])

print(f"Length r: {len(R)}")
print(f"Length mu: {len(MU)}")
print(f"Length questions: {len(QUESTIONS)}")
print(f"Length payouts: {len(PAYOUTS)}")

#####################################################################################
###
### These steps run once for all time, because it never changes during the experiment
###
#####################################################################################

# Front load the utilities -
def utility(w: float, r: float):
    """
    utility function
    w: payoff
    r: risk aversion
    """
    utility = (w ** (1 - r)) / (1 - r)
    return utility

# Front load all possible utilities
UTILITIES = {wr: utility(wr[0], wr[1]) for wr in product(PAYOUTS, R)}
print(f"Front-loaded all the utilities: {len(UTILITIES)}")

# Front load the likelihoods
def get_likelihood(a: int, q: float, k: tuple):
    """
    Likelihood function, probability of answering a (risky = 0, safe = 1)
    a: response
    Q: question, probability of high payoff
    k: model, contains prior of r and mu
    r: risk aversion prior
    mu: responsiveness to choice
    """
    r, mu = k[0], k[1]
    u10 = UTILITIES[(10, r)]
    u8 = UTILITIES[(8, r)]
    u19 = UTILITIES[(19.25, r)]
    u50 = UTILITIES[(.50, r)]
    likelihood = 1 / (1 + np.exp(-mu * (u10 * q + u8 * (1 - q) - u19 * q - u50 * (1 - q))))
    if a == 0:
        return 1 - likelihood
    elif a == 1:
        return likelihood
    else:
        return "error, answer is not binary"

LIKELIHOODS = {(a, q, _r, _mu): get_likelihood(a, q, (_r, _mu)) for a, q, _r, _mu in product(ACTIONS, QUESTIONS, R, MU)}
print(f"Front-loaded all the likelihoods: {len(LIKELIHOODS)}")

#####################################################################################
###
# Everything else depends on the priors, since those change after each choice we need to
# calculate the rest on the fly.
###
#####################################################################################

class KLInfo:
    """Calculate the KL Information for the given set of priors, actions, and questions"""
    def __init__(self, actions, questions, models, priors, likelihoods):
        self.likelihoods = likelihoods
        self.models = models
        self.priors = priors
        self.actions = actions
        self.questions = questions

        # We can still speed thing up by front loading most of this information
        d0 = models.shape[0]
        d1 = models.shape[1]

        #full_denoms is especially helpful since it can be used in the KL calculations and the prior updations
        self.full_denoms = {(a, q): self.get_denominator_full(a, q) for a, q in product(actions, questions)}
        self.denoms = {(a, q, i, j): self.get_denominator(a, q, (i, j)) for a, q, i, j in
                       product(actions, questions, range(d0), range(d1))}
        self.info = {(q, i, j): self.get_information_number(q, (i, j)) for q, i, j in
                     product(questions, range(d0), range(d1))}
        self.kl = {q: self.question_KL(q) for q in questions}

    def get_denominator_full(self, a: int, q: float):
        denom = 0
        for i, row in enumerate(self.models):
            for j, element in enumerate(row):
                m = self.models[i, j]
                denom += P[i, j] * float(self.likelihoods[a, q, m[0], m[1]])
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
        denom = self.full_denoms[(a, q)]
        i, j = k[0], k[1]
        r, mu = self.models[i, j]
        return denom - self.priors[i, j] * float(self.likelihoods[a, q, r, mu])

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
            l = float(self.likelihoods[a, q, _r, _mu])
            d = float(self.denoms[a, q, i, j])
            I += l * np.log(1 - P[i, j] * l / d)
        return I

    def question_KL(self, q: float):
        """
        Calculates Kullback-Liebler information number for a question
        Q: question, probability of high payoff
        """
        KL = 0
        for i, row in enumerate(self.models):
            for j, element in enumerate(row):
                k = (i, j)
                KL += self.priors[i, j] * self.info[q, i, j]
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
        updated_P = np.zeros(self.priors.shape)

        denom = self.full_denoms[(a, q)]
        for i, row in enumerate(self.models):
            for j, element in enumerate(row):
                m = self.models[i, j]
                updated_P[i, j] = float(self.likelihoods[a, q, m[0], m[1]]) * self.priors[i, j] / denom
        return updated_P


# Main loop
print("Entering main loop")
for i in range(4):
    kli = KLInfo(ACTIONS, QUESTIONS, M_values, P, LIKELIHOODS)
    q, inf = kli.get_next_Q()
    print(f"Next Question: {q}")
    p = kli.update_priors(0, q)