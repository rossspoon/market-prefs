import numpy as np
# import matplotlib.pyplot as plt

def utility(w: float, r: float):
    """
    utility function
    w: payoff
    r: risk aversion    
    """
    utility = (w**(1-r))/1-r
    return utility

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
    likelihood = 1/(1 + np.exp(-mu*(utility(10, r)*q+ utility(8, r)*(1-q) - utility(19.25, r)*q - utility(.5, r)*(1-q))))
    if a == 0:
        return (1-likelihood)
    elif a == 1:
        return likelihood
    else:
        return "error, answer is not binary"

def get_denominator(a: int, q: float, k: tuple, M: np.array, P: np.array):
    """
    Get's denominator for get_information_numer function
    a: response (binary)
    Q: question, probability of high payoff
    k: specified model
    M: List of all Models (r, mu)
    p: prior joint distribution of Models
    """
    denom=0
    modeli, modelj = k[0], k[1]
    for i, row in enumerate(M):
        for j, element in enumerate(row):
            if M[i,j] != M[modeli,modelj]:
                denom+= P[i,j] * get_likelihood(a, q, M[i,j])
    return denom

def get_information_number(q: float, k: tuple, M: np.array, P: np.array):
    """
    Get's denominator for get_information_numer function
    q: question, probability of high payoff
    k: specified model
    M: List of all Models (r, mu)
    p: prior joint distribution of Models
    """
    I = 0
    i,j = k[0], k[1]
    for a in range(2):
        I+= get_likelihood(a, q, M[i,j]) * np.log(1-P[i,j] * get_likelihood(a, q, M[i,j])/ get_denominator(a, q, k, M, P))
    return I

def question_KL(q: float, M: np.array, P: np.array):
    """
    Calculates Kullback-Liebler information number for a question
    Q: question, probability of high payoff
    M: List of all Models (r, mu)
    p: prior joint distribution of Models
    """
    KL=0
    for i, row in enumerate(M):
        for j, element in enumerate(row):
            k = (i,j)
            KL+= P[i,j] * get_information_number(q, k, M, P) 
    return KL

def get_next_Q(Q: list, M: np.array, P: np.array):
    """
    Get's the next question in the sequence
    Q_list: list of questions, probability of high payoff
    M: List of all Models (r, mu)
    P: prior joint distribution of Models
    """
    next_Q = (-1, -1)
    for idx, q in enumerate(Q):
        I = question_KL(q, M, P)
        if I > next_Q[1]:
            next_Q = (idx, I)
    return next_Q

def prior_update_denominator(M, a, q, P):
    """"
    Updates gets denominator
    M: Matrix containing values of r(risk aversion parameter) and mu (responsiveness to choice)
    a: question response
    q: question asked
    P: Matrix containing the probabilities of each value of M
    """
    denom=0
    for i, row in enumerate(M):
        for j, element in enumerate(row):
            denom+= P[i,j] * get_likelihood(a, q, M[i,j])
    return denom


def update_priors(M, a, q, P):
    """
    Updates the posterior distribution for r and mu
    M: Matrix containing values of r(risk aversion parameter) and mu (responsiveness to choice)
    a: question response
    q: question asked
    P: Matrix containing the probabilities of each value of M
    """
    denom = prior_update_denominator(M, a, q, P)
    for i, row in enumerate(M):
        for j, element in enumerate(row):
            P[i, j] = get_likelihood(a, q, M[i,j]) * P[i, j]/ denom
    return P

"Sets the priors"
questions = np.arange(0,1.01,.01)
r = np.arange(-1, 1, 0.05)
mu = np.arange(0, 2, 0.1)
pr = 1 / len(r)
pmu = 1 / len(mu)

P = np.zeros((len(r), len(mu)))
M_values = np.empty((len(r), len(mu)), dtype=object)

for i in range(len(r)):
    for j in range(len(mu)):
        P[i, j] = pr * pmu
        M_values[i, j] = (r[i], mu[j])

"""Main loop"""
for num in range(4):
    q_index, information_number = get_next_Q(questions, M_values, P)
    q = questions[q_index]
    print("Next question index:", questions[q_index])
    P = update_priors(M_values, 0, q, P)
    
