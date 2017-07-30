import itertools
import warnings

"""
File containing the equivalent to MATSim classes

author: Haris Ballis (25/07/2017)
"""
class Leg(object):
    """ Plans class """

    def __init__(self, **kwargs):
        prop_defaults = {
            'mode': 'car'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        self.route = None


class Route(object):
    """ Plans class """

    def __init__(self, **kwargs):
        prop_defaults = {
            'type': 'links'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        self.value = None


class Agent(object):
    """ Agent class """

    def __init__(self,plans=list(), **kwargs):
        prop_defaults = {
            'id': None,
            'home_xy': None
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        self.plans = plans


class Activity(object):
    """ Activities class """

    def __init__(self, **kwargs):
        prop_defaults = {
            'type': 'undefined',
            'link': None,
            'x': None,
            'y': None,
            'duration': None,
            'end_time': None
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))


class Stage(object):
    """ Stage class
        Stage is a part of a trip between 2 activities
    """

    activities = [Activity(), Activity()]
    legs = [Leg()]

    def __init__(self, activities=activities, legs=legs):
        if len(activities) != 2:
            raise ValueError('Exactly two activities are required at least')
        elif len(legs) < 1:
            raise ValueError('At least one leg is required')
        else:
            self.activities = activities
            self.legs = legs

            self.orig_act = activities[0]
            self.dest_act = activities[1]

            chain = list()
            chain.append(activities[0])
            chain.append(*legs)
            chain.append(activities[1])
            self.chain = chain


class TripChain(object):
    """
    Args:
        stages (list): List of stage objects

    Attributes:
        stages (list): Sequence of stages

    """

    def __init__(self, stages, **kwargs):
        prop_defaults = {
            'selected': 'no'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        self.stages = stages
        self.chain = self.chain_from_stages(stages)

    def chain_from_stages(self, stages):
        chain_tmp = list()
        for s in stages:
            for c in s.chain:
                chain_tmp.append(c)
        # Check for consecutive duplicates
        chain = [x[0] for x in itertools.groupby(chain_tmp)]
        return chain

    def append_stage(self, stage):
        stages = self.stages
        # The last activity of the former trip chain and the
        # first activity of the new stage must be the same
        act_prev = stages[-1].chain[-1]
        act_next = stage.chain[0]

        if act_prev == act_next:
            stages.append(stage)
            self.chain = self.chain_from_stages(stages)
        else:
            warnings.warn('Last activity of previous stage '
                          'does not match first activity of current')


class Plan(object):

    def __init__(self, trip_chain, **kwargs):
        prop_defaults = {
            'selected': 'no'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        self.trip_chain = trip_chain

