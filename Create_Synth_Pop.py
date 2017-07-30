import sys
import pandas as pd
import numpy as np
from matsim import Agent, Activity, Plan, Stage, TripChain, Leg, Route
import random
from lxml.etree import ElementTree, Element, SubElement, tostring
import datetime
import inspect
import warnings


def datetime_to_secs(time):
    if type(time) is datetime.time:
        secs = time.hour * 3600 + time.minute * 60 + time.second
        return secs
    else:
        pass
        # print('Provide a datetime.time var')


def rand_normal_time(time, dev):
    # Returns a normally distributed random number and converts it into time
    # Negative time gets converted to 0
    mean = datetime_to_secs(datetime.datetime.strptime(time, '%H:%M').time())
    std = datetime_to_secs(datetime.datetime.strptime(dev, '%H:%M').time())
    # Draw from a normal distr
    time_secs = np.random.normal(loc=mean, scale=std)
    if time_secs > 0:
        rand_time = str(datetime.timedelta(seconds=time_secs)).split('.')[0]
    else:
        warnings.warn('Negative time was calculated, returned 0')
        rand_time = 0
    return rand_time


def write_xml_elem(c, d, p):
    import inspect

    class_name = c.__class__.__name__

    for attr, v in c.__dict__.items():
        if isinstance(v, list):
            if inspect.isclass(v[0]):
                parent_elem = d[class_name]
                SubElement(parent_elem, class_name.lower())
                for e in v:
                    write_xml_elem(e, d, parent_elem)


def write_xml_attrs(cls, xml_elem):
    for attr, v in cls.__dict__.items():
        if isinstance(v, (int, float, str)):
            if v:
                xml_elem.set(attr, str(v))

    
def build_pop_xml(pop):
    xml_root = Element('plans')
    for person in pop:
        xml_agent = SubElement(xml_root, 'person')
        write_xml_attrs(person, xml_agent)
        for plan in person.plans:
            xml_plan = SubElement(xml_agent, 'plan')
            write_xml_attrs(plan, xml_plan)
            for stage in plan.trip_chain.stages:
                # Origin Activity
                xml_activity = SubElement(xml_plan, 'act')
                write_xml_attrs(stage.orig_act, xml_activity)
                for leg in stage.legs:
                    xml_leg = SubElement(xml_plan, 'leg')
                    write_xml_attrs(leg, xml_leg)
                    route = leg.route
                    if route:
                        xml_route = SubElement(xml_leg, 'route')
                        write_xml_attrs(route, xml_route)
            # The destination activity is required to be written in the xml
            # only for the last stage since the dest_act is the orig_act of the nect stage
            # Destination activity
            xml_activity = SubElement(xml_plan, 'act')
            write_xml_attrs(stage.dest_act, xml_activity)
    return xml_root


def read_centroids(path):
    df = pd.read_csv(path, index_col=3)
    df = df[['x', 'y']]
    return df


def read_demand_mat(path):
    df = pd.read_csv(path, delimiter=';', index_col=[0, 1, 2])
    return df


def read_info_mat(path):
    df = pd.read_csv(path, delimiter=';', index_col=0)
    return df


def prepare_demand_mat(mat_dem, mat_info):
    df = mat_dem.join(mat_info.NAME)
    df.reset_index(inplace=True)
    df = df.drop('MATRIXNO', 1)
    df['NAME'] = df['NAME'].astype('category')
    df = df.set_index(['NAME', 'FROMNO', 'TONO'])
    df.sort_index(inplace=True)

    demand = df.loc[['HBW_C', 'HBW_X', 'HBEDU_C', 'HBEDU_X', 'HBO_C',
                     'HBO_X', 'HBSH_C', 'HBSH_X', 'NHB_C', 'NHB_X'], :]

    # Cleaning
    demand.reset_index(inplace=True)
    demand = demand.assign(Purpose=lambda x: x.NAME.str.split('_').str[0])
    demand = demand.assign(Source=lambda x: x.NAME.str.split('_').str[1])
    demand.drop('NAME', axis=1, inplace=True)

    demand.rename(columns={'FROMNO': 'From_Node', 'TONO': 'To_Node', 'VALUE': 'Trips'}, inplace=True)
    demand.Purpose = demand.Purpose = demand.Purpose.astype('category')
    demand.Source = demand.Source.astype('category')

    demand.set_index(['Purpose', 'Source', 'From_Node', 'To_Node'], inplace=True)

    return demand


def create_activity(acts_time_info, act_type, xy):
    keys = list(acts_time_info[act_type].keys())
    k_time = keys[0]  # k_time is depTime or duration
    k_dev = keys[1]  # k_dev is st.dev of depTime or duration

    time = acts_time_info[act_type][k_time]
    dev = acts_time_info[act_type][k_dev]

    end_time = None
    duration = None

    rand_time = rand_normal_time(time, dev)

    if k_time == 'depTime':
        end_time = rand_time
    else:
        # Duration is defined
        duration = rand_time
        
    x, y = xy

    # TODO must generate random points in the zone
    act = Activity(type=act_type, x=x, y=y, end_time=end_time, duration=duration)
    return act

def randomise_coords(xy, dist):
    x, y = xy
    x = x + random.uniform(-dist, dist)
    y = y + random.uniform(-dist, dist)
    xy = x, y
    return xy

# Not really flexible yet
def build_pop(demand, zone_coords, acts_time_info):
    rand_dist = 500  # Create random points around zone coords
    pop = []
    agent_id = 1
    # Keep only the HBW trips (should be HBW_FH actually)
    trips = demand.xs(['HBW', 'C'], level=[0,1], drop_level=False)

    # Destinations of NHB trips
    nhb_trips = demand.xs(['NHB', 'C'], level=[0, 1])
    # TODO We have way too few nhb trips that's why ceiling is applied
    nhb_trips = nhb_trips.apply(np.ceil)
    nhb_trips = nhb_trips.mul(50)

    for trip in trips.iteritems():
        idx = trip[0]
        val = trip[1]
        # Dictionary with the trips info
        d = dict(zip(trips.index.names, idx))
        for t in range(0, int(val)):
            # Create the agent
            agent = Agent(id=agent_id)
            # Create the activities
            # Stage 1: Home to Work
            # First activity home

            xy = tuple(zone_coords.loc[d['From_Node']])
            xy = randomise_coords(xy, rand_dist)

            # Set the home coords of the agent
            agent.home_xy = xy
            act_orig = create_activity(acts_time_info, 'home', xy)

            xy = tuple(zone_coords.loc[d['To_Node']])
            xy = randomise_coords(xy, rand_dist)

            act_dest = create_activity(acts_time_info, 'work', xy)
            
            # Create the leg
            leg = Leg(mode='car')
            # Stage is a trip between 2 activities
            stage = Stage(activities=[act_orig, act_dest], legs=[leg])

            # Create the first trip chain
            stages = list()
            stages.append(stage)
            trip_chain = TripChain(stages)

            # First naive implementation of a trip chain
            # Stage 2: Work to Leissure
            # The NHB trips originating from the work location of the previous stage
            # will be chained to the HBW trips of the previous stage
            oriz_zone = d['From_Node']
            nhb_dests = nhb_trips.xs(oriz_zone, level=0)
            if not nhb_dests.empty:
                if nhb_dests.sum() >= 1:
                    # The previous stage's dest must be the next's origin
                    act_orig = act_dest

                    # Pick a random destination weighted by the number of trips
                    sample = nhb_dests.sample(1, weights=nhb_dests)
                    dest_zone = sample.index[0]
                    # Remove the nhb trip from the nhb matrix
                    nhb_trips.loc[oriz_zone, dest_zone] = nhb_dests.loc[dest_zone] - 1

                    x, y = zone_coords.loc[dest_zone]
                    x = x + random.uniform(-rand_dist, rand_dist)
                    y = y + random.uniform(-rand_dist, rand_dist)
                    xy = x, y

                    act_dest = create_activity(acts_time_info, 'leisure', xy)

                    # Create the leg
                    leg = Leg(mode='car')
                    # Stage is a trip between 2 activities
                    stage = Stage(activities=[act_orig, act_dest], legs=[leg])

                    trip_chain.append_stage(stage)

            # all agents return home, we add this manually
            act_orig = act_dest
            x, y = agent.home_xy
            act_dest = Activity(type='home', x=x, y=y, end_time=None, duration=None)

            # Create the leg
            leg = Leg(mode='car')
            # Stage is a trip between 2 activities
            stage = Stage(activities=[act_orig, act_dest], legs=[leg])
            trip_chain.append_stage(stage)

            # Create the plans
            plan = Plan(selected='yes', trip_chain=trip_chain)
            agent.plans = [plan]

            pop.append(agent)
            agent_id += 1

    return pop


def main():
    path_demand = '../Demand/matrices_demand.txt'
    path_info = '../Demand/matrices_info.txt'
    path_centroids = '../Network/Zones/zones_centroids_EPSG32636.csv'

    dem = read_demand_mat(path_demand)
    dem_info = read_info_mat(path_info)
    zone_coords = read_centroids(path_centroids)

    # Clean the demand matrix
    demand = prepare_demand_mat(dem, dem_info)
    # demand_synthPop = demand.xs(['HBW', 'C'], level=[0, 1], drop_level=False)
    idx = pd.IndexSlice
    demand_synthPop = demand.loc[idx[['HBW', 'NHB'], 'C'], :]

    # Dictionary with departure times and standard devs
    acts_time_info = {'home': {'depTime': '08:00',
                                     'dev': '00:30'},
                           'work':  {'depTime': '17:00',
                                     'dev': '00:30'},
                       'leisure':   {'depTime': '19:00',
                                     'dev': '01:00'}
                      }
    # Create integer trips
    # TODO improve method
    trips = demand_synthPop.Trips.round()

    # exclude 0 trips
    trips = trips[trips != 0]

    pop = build_pop(trips, zone_coords, acts_time_info)

    fxml = build_pop_xml(pop)

    with open('pop_incrNHB.xml', 'wb') as f:
        s = tostring(fxml, encoding="UTF-8", xml_declaration=True, pretty_print=True,
                     doctype='<!DOCTYPE plans SYSTEM "http://www.matsim.org/files/dtd/plans_v4.dtd" >')
        f.write(s)

if __name__ == "__main__":
    main()
