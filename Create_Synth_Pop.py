
# Author Haris Ballis 23/07/2017 

import pandas as pd
import numpy as np
from xml.etree.ElementTree import Element, SubElement, tostring

class act(object):
    """ Activities class """    
    def __init__(self, **kwargs):
        prop_defaults = {
            'type': 'undefined', 
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

class plan(object):
    """ Plans class """
    def __init__(self, **kwargs):
        prop_defaults = {
            'selected': 'no'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

class person(object):
    """ Agents class """
    def __init__(self, **kwargs):
        prop_defaults = {}

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

# Inputs
zone_centroids = pd.read_csv('../Network/Zones/zones_centroids_EPSG6312.csv', index_col=3)
zone_centroids = zone_centroids[['x', 'y']]
zone_centroids.head()

mats = pd.read_csv('../Demand/matrices_demand.txt', delimiter=';', index_col=[0,1,2])
mats_info = pd.read_csv('../Demand/matrices_info.txt', delimiter=';', index_col=0)

df = mats.join(mats_info.NAME)
df.reset_index(inplace=True)
df = df.drop('MATRIXNO', 1)
df['NAME'] = df['NAME'].astype('category')
df = df.set_index(['NAME', 'FROMNO', 'TONO'])
df.sort_index(inplace=True)
demand = df.loc[['HBW_C', 'HBW_X', 'HBEDU_C', 'HBEDU_X', 'HBO_C', 'HBO_X', 'HBSH_C', 'HBSH_X', 'NHB_C', 'NHB_X',],:]

# Cleaning
demand.reset_index(inplace=True)
demand = demand.assign(Purpose = lambda x: x.NAME.str.split('_').str[0])
demand = demand.assign(Direction = lambda x: x.NAME.str.split('_').str[1])
demand.drop('NAME', axis=1, inplace=True)

demand.rename(columns={'FROMNO': 'From_Node', 'TONO': 'To_Node', 'VALUE': 'Trips'}, inplace=True)
demand.Purpose.astype('category')
demand.Direction.astype('category')

demand.set_index(['Purpose', 'Direction', 'From_Node', 'To_Node'], inplace=True)


# ### Test demand
demand_synthPop = demand.xs(['HBW', 'C'], level=[0,1], drop_level=False)

# Create integer trips
# To-Do improve method
trips = demand_synthPop.Trips.round()

# exclude 0 trips
trips = trips[trips!=0]


#print(trip[0])

#temp
#==============================================================================
# elems = {'person': person,
#          'plan': plan,
#          'activity': activity,
#          'leg': leg
#         }
# 
# attrs = {}
# attrs['person'] = {'id': agent_id} 
# attrs['activity'] = {'type': activity_type, 
#                         'x': coord_x,
#                         'y': coord_y
#                     }
# 
# attrs['plan'] = {'selected': '1'} 
# attrs['leg'] = {'mode': mode} 
# 
# 
# # In[126]:
# 
# 
# def build_pop_xml(elems, attrs):
#     root = Element('population')
#     person = SubElement(root, 'person')
#     plan = SubElement(person, 'plan')
#     activity = SubElement(person, 'act')
#     leg = SubElement(person, 'leg')
# 
#     for k1, elem in elems.items():
#         for k2, attr in attrs[k1].items():
#             elem.set(k2, attr)
# 
#     print(tostring(root))
# 
# 
# # <population >
# # <person id= "1">
# # <plan selected= "yes " score= " 93.2987721 ">
# # <act type= " home " link= "1" end_time= " 07:16:23 " />
# # <leg mode= "car ">
# # <route type= " links ">1 2 3</ route >
# # </ leg >
# # <act type= " work " link= "3" end_time= " 17:38:34 " />
# # <leg mode= "car ">
# # <route type= " links ">3 1</ route >
# # </ leg >
# # <act type= " home " link= "1" />
# # </ plan >
# # </ person >
# # <person id= "2">
# # <plan selected= "yes " score= " 144.39002 ">
# # ...
# # </ plan >
# # </ person >
# # </ population >
# 
# # main_nodes = pd.read_csv(r'C:\Users\haris.ballis\OneDrive - Transport Systems Catapult\Personal\PhD\Model_Cyprus\Data\Network\Zones\nodes_in-fully-detailed-area.csv')
# # mn = main_nodes.NO.tolist()
# 
# # idxsl = pd.IndexSlice
# # int_demand = demand.loc[idxsl[:, :, mn, mn], :]
# 
# # In[ ]: 
#==============================================================================
