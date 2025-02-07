# Group 4 - Intelligent Negotiation Agent Report

Gabriel Mazor, gabriel.mazor@post.runi.ac.il, Shannie Chacham, shannie.chacham@post.runi.ac.
## Introduction
We started with playing with the platform and analyzing the results, understanding when the agent fail to land a good deal for itself and looking for creative ways to overcame each use case where it fails.
## High-level Overall Description

### Descussions
Let's not accept before 0.9
Lets not accept offers lower than nash or kalai to have more advantage on average.

## Component Description
### Key Defenitions
`advantage = utility(offer) - reserved_value` <br>
`predicted advantage = opponent_utility - predicted_reserved_value` <br>
`rv` - agent's reserved value (ellaborate) <br>
`nash_point` <br>
`kalai_point` <br>
`min_offer` <br>
`pareto_outcomes` <br>
`next_offer` <br>

#### Aspiration Function
A centric heuristic we are using for our agent is the aspiration function, which plays a crucial role in our agent’s decision-making process, shaping both our acceptance and bidding strategies and also the way we model the opponent’s decision-making. It defines our utility threshold over time, influencing which offers we propose and which we accept as the negotiation progresses.
$$ asp(t) = (mx-rv)(1-t^e) +rv $$
Where `t` is relative time [0,1], `mx` is maximal possible utility, `rv` is the reserved value and `e` is the concession exponent, whivh controls how much we lower our treshold over time.


### Acceptance Strategy
Through testing the negotiation platform, we identified a clear pattern.
After testing and playing with the negotiation platform, we observed a clear pattern: regardless of opponents’ strategy, they tend to concede over time, which results in better offers for our utility as the negotiation progresses. Accepting early offers leads to suboptimal outcomes, as we miss out on potentially better agreements later on. 

The observation led to a key decision in our acceptance strategy, we separate our acceptance strategy into three main segments: 
1.	Early segment – when negotiation `relative_time < 0.9`
2.	Critical segment – when negotiation `relative_time >= 0.9`
3.	Last resort segment – relaxing acceptance at the real last steps.

Another critical part that guides us through the whole acceptance process is the aspiration function we defined before, which is calculated at the first step each time the `__call__` function is called. The agent will never accept offers lower than the current aspiration threshold.

Our acceptance strategy function was built from scratch, following the logic below:

1.	Early segment
    For `relative_time < 0.9`, we **reject** nearly all offers as we anticipate better ones arriving as the negotiation continues.
    The **only** offers we **accept** at this stage are offers that give us a 1.5 times higher advantage `(advantage = utility(offer) - reserved value)` than the predicted advantage the opponent has.

2.	Critical segment
    For `relative_time > 0.9`, our strategy is broken down into multiple conditions.
    - **Reject** offers lower than the `min_offer`
    - If the offer’s utility is above the current aspiration threshold:
      - If the offer is on the Pareto frontier -> **Accept**
      - Otherwise, if the set of Pareto outcomes exists:
        - Find a candidate Pareto offer with the minimum difference in the opponent’s utility from the offer he just made. 
          - If our utility for the candidate offer is lower than the offer the opponent made -> **Accept**
          - Otherwise, if the candidate’s offer utility is above our current threshold, save this offer as the `next_offer` we are going to bid on.
          - **Reject** all other offers

    The candidate offer we identified enables our agent to maximize its utility by proposing a subsequent offer that maintains a similar utility score for the opponent while optimizing our own. This approach allows us to secure a significantly better offer than what we would have accepted based solely on the threshold score without damaging the opponent’s utility and ultimately providing us with a greater advantage.

3.	Last resort segment
    To ensure we are not losing agreement above our reserved value at the real last steps we relaxing our acceptance policy a bit.
    - We consider outcomes below the `min_offer` in the last 10 steps.
    - In the last two steps, we prioritize securing agreements above our reserved value. To avoid unnecessary rejection, we **accept** any offer above our reserved value.

### Bidding Strategy

### Opponent Model

## Qunatifing the Agent's Perfomance

## Future Perspective