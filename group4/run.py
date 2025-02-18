import copy
import matplotlib.pyplot as plt
from negmas.sao import SAOMechanism
from anl.anl2024.runner import mixed_scenarios
from anl.anl2024.negotiators.builtins import Linear, Conceder, Boulware
from group4 import Group4
from hard_chaos import HardChaosNegotiator
from shochan import Shochan
from missg import MissG
import random

plt.tight_layout()

for i in range(10):
    # create a scenario
    s = mixed_scenarios(1)[0]
    
    # copy ufuns and set rv to 0 in the copies
    ufuns0 = [copy.deepcopy(u) for u in s.ufuns]
    for u in ufuns0:
        u.reserved_value = 0.0
    
    # create the negotiation mechanism
    session = SAOMechanism(n_steps=1000, outcome_space=s.outcome_space)
    
    # add negotiators. Remember to pass the opponent_ufun in private_info
    session.add(Group4(name="Group4", private_info=dict(opponent_ufun=ufuns0[1])), ufun=s.ufuns[0])
    
    # add a random opponent
    # Ensure opponent_ufun is passed correctly
    session.add(MissG(name="MissG", private_info=dict(opponent_ufun=ufuns0[0])), ufun=s.ufuns[1])
    
    # run the negotiation and plot the results
    session.run()
    session.plot()
    plt.savefig(f"{i+1}_group4_vs_MissG.png", bbox_inches='tight')