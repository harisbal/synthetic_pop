import pandas as pd
import numpy as np
from xml.etree.ElementTree import ElementTree, Element, SubElement, tostring
import datetime
from matsim import Agent, Activity, Plan, Stage, Leg, Route

def datetime_to_secs(time):
    if type(time) is datetime.time:
        secs = time.hour * 3600 + time.minute * 60 + time.second
        return secs
    else:
        pass
        # print('Provide a datetime.time var')


def rand_normal_time(time, dev):
    mean = datetime_to_secs(datetime.datetime.strptime(time, '%H:%M').time())
    std = datetime_to_secs(datetime.datetime.strptime(dev, '%H:%M').time())
    # Draw from a normal distr
    time_secs = np.random.normal(loc=mean, scale=std)
    rand_time = str(datetime.timedelta(seconds=time_secs)).split('.')[0]
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
        if not isinstance(v, list):
            if v:
                xml_elem.set(attr, str(v))

    
def build_pop_xml(pop):
    xml_root = Element('population')
    for person in pop:
        xml_agent = SubElement(xml_root, 'person')
        write_xml_attrs(person, xml_agent)
        for plan in person.plans:
            xml_plan = SubElement(xml_agent, 'plan')
            write_xml_attrs(plan, xml_plan)
            for stage in plan.trip_chain:
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
                # Destination activity
                xml_activity = SubElement(xml_plan, 'act')
                write_xml_attrs(stage.dest_act, xml_activity)
    return xml_root


def read_centroids(path='../Network/Zones/zones_centroids_EPSG6312.csv'):
    df = pd.read_csv(path, index_col=3)
    df = df[['x', 'y']]
    return df


def read_demand_mat(path='../Demand/matrices_demand.txt'):
    df = pd.read_csv(path, delimiter=';', index_col=[0, 1, 2])
    return df


def read_info_mat(path='../Demand/matrices_info.txt'):
    df = pd.read_csv(path, delimiter=';', index_col=0)
    return df


def prepare_demand_mat(mat_dem, mat_info):
    df = mat_dem.join(mat_info.NAME)
    df.reset_index(inplace=True)
    df = df.drop('MATRIXNO', 1)
    df['NAME'] = df['NAME'].astype('category')
    df = df.set_index(['NAME', 'FROMNO', 'TONO'])
    df.sort_index(inplace=True)

    demand = df.loc[['HBW_C', 'HBW_X', 'HBEDU_C', 'HBEDU_X', 'HBO_C', 'HBO_X', 'HBSH_C', 'HBSH_X', 'NHB_C', 'NHB_X', ],
             :]

    # Cleaning
    demand.reset_index(inplace=True)
    demand = demand.assign(Purpose=lambda x: x.NAME.str.split('_').str[0])
    demand = demand.assign(Direction=lambda x: x.NAME.str.split('_').str[1])
    demand.drop('NAME', axis=1, inplace=True)

    demand.rename(columns={'FROMNO': 'From_Node', 'TONO': 'To_Node', 'VALUE': 'Trips'}, inplace=True)
    demand.Purpose.astype('category')
    demand.Direction.astype('category')

    demand.set_index(['Purpose', 'Direction', 'From_Node', 'To_Node'], inplace=True)

    return demand

# Not really flexible yet
def build_pop(trips, zone_coords, dep_times_devs):
    pop = []
    agent_id = 1
    for trip in trips.iteritems():
        idx = trip[0]
        val = trip[1]
        # Dictionary with the trips info
        d = dict(zip(trips.index.names, idx))
        for t in range(0, int(val)):
            # Create the agent
            agent = Agent(id=agent_id)

            # Create the activities
            # Get Node's coords
            depTime_home, depTime_home_dev = dep_times_devs[0]
            x, y = zone_coords.loc[d['From_Node']]
            end_time = rand_normal_time(depTime_home, depTime_home_dev)
            # TODO must generate random points in the zone
            act_orig = Activity(type='home', x=x, y=y, end_time=end_time)

            depTime_work, depTime_work_dev = dep_times_devs[1]
            x, y = zone_coords.loc[d['To_Node']]
            end_time = rand_normal_time(depTime_work, depTime_work_dev)
            act_dest = Activity(type='work', x=x, y=y, end_time=end_time)

            # Create the leg
            leg = Leg(mode='car')
            # Stage is a trip between 2 activities
            stage = Stage(activities=[act_orig, act_dest], legs=[leg])
            # Create the plans
            trip_chain = [stage]
            plan = Plan(selected='yes', trip_chain=trip_chain)
            agent.plans = [plan]

            pop.append(agent)
            agent_id += 1

    return pop


def main():
    dem = read_demand_mat()
    dem_info = read_info_mat()
    zone_coords = read_centroids()

    demand = prepare_demand_mat(dem, dem_info)

    demand_synthPop = demand.xs(['HBW', 'C'], level=[0, 1], drop_level=False)

    # Departure time
    depTime_home = '08:00'  # 8 hours
    depTime_home_dev = '00:30'  # deviation

    depTime_work = '17:00'  # 8 hours
    depTime_work_dev = '00:30'  # deviation

    dep_times_devs = [(depTime_home, depTime_home_dev),
                      (depTime_work, depTime_work_dev)]

    # Create integer trips
    # TODO improve method
    trips = demand_synthPop.Trips.round()

    # exclude 0 trips
    trips = trips[trips != 0]
    # !!!!!!!!!!!!!!!!
    trips = trips.head(1)

    pop = build_pop(trips, zone_coords, dep_times_devs)

    xml = build_pop_xml(pop)

    ElementTree(xml).write('pop.xml')


if __name__ == "__main__":
    main()
