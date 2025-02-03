"""
**Submitted to ANAC 2024 Automated Negotiation League**
*Team* type your team name here
*Authors* type your team member names with their emails here

This code is free to use or update given that proper attribution is given to
the authors and the ANAC 2024 ANL competition.
"""
import random
from scipy.optimize import curve_fit
import numpy as np
from negmas.outcomes import Outcome
from negmas.sao import ResponseType, SAONegotiator, SAOResponse, SAOState


class Group4(SAONegotiator):
    """
    Your agent code. This is the ONLY class you need to implement
    """

    rational_outcomes = tuple()
    opponent_outcomes = tuple()
    joint_outcomes = tuple()
    opponent_reserved_value = 0.0

    def on_preferences_changed(self, changes):
        """
        Called when preferences change. In ANL 2024, this is equivalent with initializing the agent.

        Remarks:
            - Can optionally be used for initializing your agent.
            - We use it to save a list of all rational outcomes.

        """
        self.exp = 2.0
        self.opponent_ufuns = []
        self.opponent_ufuns_times = []
        self.opponent_exp = []
        self.opponent_strategy = None
        self.joint_utils = []

        # If there a no outcomes (should in theory never happen)
        if self.ufun is None:
            return

        self.rational_outcomes = [
            _
            for _ in self.nmi.outcome_space.enumerate_or_sample()  # enumerates outcome space when finite, samples when infinite
            if self.ufun(_) > self.ufun.reserved_value
        ]

        # Estimate the reservation value, as a first guess, the opponent has the same reserved_value as you
        self.opponent_outcomes_reserved_value = self.ufun.reserved_value

    def __call__(self, state: SAOState) -> SAOResponse:
        """
        Called to (counter-)offer.

        Args:
            state: the `SAOState` containing the offer from your partner (None if you are just starting the negotiation)
                   and other information about the negotiation (e.g. current step, relative time, etc).
        Returns:
            A response of type `SAOResponse` which indicates whether you accept, or reject the offer or leave the negotiation.
            If you reject an offer, you are required to pass a counter offer.

        Remarks:
            - This is the ONLY function you need to implement.
            - You can access your ufun using `self.ufun`.
            - You can access the opponent's ufun using self.opponent_ufun(offer)
            - You can access the mechanism for helpful functions like sampling from the outcome space using `self.nmi` (returns an `SAONMI` instance).
            - You can access the current offer (from your partner) as `state.current_offer`.
              - If this is `None`, you are starting the negotiation now (no offers yet).
        """
        offer = state.current_offer

        self.update_partner_reserved_value(state)

        # if there are no outcomes (should in theory never happen)
        if self.ufun is None:
            return SAOResponse(ResponseType.END_NEGOTIATION, None)

        # Determine the acceptability of the offer in the acceptance_strategy
        if self.acceptance_strategy(state):
            return SAOResponse(ResponseType.ACCEPT_OFFER, offer)

        # If it's not acceptable, determine the counter offer in the bidding_strategy
        return SAOResponse(ResponseType.REJECT_OFFER, self.bidding_strategy(state))

    def acceptance_strategy(self, state: SAOState) -> bool:
        """
        This is one of the functions you need to implement.
        It should determine whether or not to accept the offer.

        Returns: a bool.
        """
        assert self.ufun

        offer = state.current_offer
        treshold = aspiration_function(state.relative_time, 1.0, self.ufun.reserved_value, self.exp)
        
        if self.ufun(offer) >= treshold:
            return True
        return False
        # this acceptance as it is now, doesn't consider the opponent's strategy, ufun or advantage. Concider adding

    def bidding_strategy(self, state: SAOState) -> Outcome | None:
        """
        This is one of the functions you need to implement.
        It should determine the counter offer.

        Returns: The counter offer as Outcome.
        """
        if state.relative_time > 0.5:
            if self.joint_outcomes:
                threshold = aspiration_function(state.relative_time, 1.0, self.opponent_reserved_value, self.exp)
                last = len(self.joint_outcomes) - 1
                idx = max(0, min(last, int(threshold * last)))
                outcome = self.joint_outcomes[idx]
                return outcome

        # if no joint outcomes, return the offer best for us
        return self.ufun.best() 
    
    def update_partner_reserved_value(self, state: SAOState) -> None:
        """This is one of the functions you can implement.
        Using the information of the new offers, you can update the estimated reservation value of the opponent.

        returns: None.
        """
        assert self.ufun and self.opponent_ufun

        offer = state.current_offer
        if offer is None:
            return
        
        last_rv = self.opponent_reserved_value
        # update the opponent's ufun and the time it was updated
        self.opponent_ufuns.append(self.opponent_ufun(offer))
        self.opponent_ufuns_times.append(state.relative_time)

        bounds = ((0.2, 0.0), (5.0, min(self.opponent_ufuns)))

        # fitting curve to the opponent's ufuns
        if(len(self.opponent_ufuns) > 5):
            optimal_vals, _ = curve_fit(
                lambda t, e, rv: aspiration_function(t, self.opponent_ufuns[0], rv, e),
                self.opponent_ufuns_times, self.opponent_ufuns, bounds=bounds
            )
            # update the opponent's reserved value based on the fitted curve
            self.opponent_reserved_value = optimal_vals[1]
            self.opponent_exp.append(optimal_vals[0])

            # classify the opponent's strategy based on the mean of the last 5 exp values
            lr = 0.1
            if np.mean(self.opponent_exp[-5:]) < 1.0:
                self.opponent_strategy = "Conceder"
                self.exp -= lr * self.opponent_exp[-1] if self.exp > self.opponent_exp[-1] else self.exp
            else:
                self.opponent_strategy = "Boulware"
                self.exp += lr * self.opponent_exp[-1] if self.exp < self.opponent_exp[-1] else self.exp

        else:
            self.opponent_reserved_value = min(self.opponent_ufuns) / 2

        # update rational_outcomes by removing the outcomes that are below the reservation value of the opponent
        if last_rv < self.opponent_reserved_value:
            # if rv decreased, filter from the complete outcome space
            self.opponent_outcomes = [
                _
                for _ in self.nmi.outcome_space.enumerate_or_sample()  # enumerates outcome space when finite, samples when infinite
                if self.opponent_ufun(_) > self.opponent_reserved_value
            ]
        else:
            self.opponent_outcomes = [
                _
                for _ in self.opponent_outcomes
                if self.opponent_ufun(_) > self.opponent_reserved_value
            ]

        # get a list of both outcomes intersection
        self.joint_outcomes = list(set(self.rational_outcomes) & set(self.opponent_outcomes))

        # sort the joint outcomes based on the utility function
        self.joint_outcomes.sort(key=lambda o: self.ufun(o), reverse=True)
        self.joint_utils = [(float(self.ufun(o)), float(self.opponent_ufun(o)), o) for o in self.joint_outcomes]


# Helper functions
def aspiration_function(t, max, rv, e):
    """A monotonically decrasing curve starting at max (t=0) and ending at rv (min) (t=1)"""
    return (max-rv) * (1.0 -np.power(t, e)) + rv


# if you want to do a very small test, use the parameter small=True here. Otherwise, you can use the default parameters.
if __name__ == "__main__":
    from .helpers.runner import run_a_tournament

    run_a_tournament(Group4, small=True, debug=False)