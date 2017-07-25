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

    def __init__(self, **kwargs):
        prop_defaults = {
            'id': 'non_defined'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        plans = list()
        plans.append(Plan())
        self.plans = plans


class Activity(object):
    """ Activities class """

    def __init__(self, **kwargs):
        prop_defaults = {
            'type': 'undefined',
            'link': None,
            'x': None,
            'y': None,
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


class Plan(object):
    trip_chain = list()
    trip_chain.append(Stage())

    def __init__(self, trip_chain=trip_chain, **kwargs):
        prop_defaults = {
            'selected': 'no'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        self.trip_chain = trip_chain

        # def append_stage(self, stage):
        #     tc = self.trip_chain
        #     # The last activity of the former trip chain and the
        #     # first activity of the new stage must be the same
        #     act_old = tc[-1].chain[-1]
        #     act_new = stage.chain[0]
        #
        #     # To-DO this comparison wont work!
        #      if act_old == act_new:
        #         tc = tc.append(stage[1:])
        #         self.trip_chain = tc