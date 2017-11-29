from django.db import models
from pull import *




def push_processed_data(dataset, i, types, data):

    if dataset.property_set.filter(name = str(i) + "_" + str(types)):

        v = dataset.property_set.filter(name = str(i) + "_" + str(types))[0]
        v.description = repr(data)
        v.save()

    else:
        if types == "1":
             prop  = make_mc(dataset, i, types)
             prop.description = repr(data)
             prop.save()

        if types == "0":
            prop = make_cat(dataset, i, types)
            prop.description = repr(data)
            prop.save()

# push id object settings using netid x3. takes netid, dictionary
# and pushes dictionary to id object settings
def push_settings(netid, dicty):
    id_object = get_id(netid)
    tempsettings = pull_settings(netid)
    if tempsettings:
        for each in dicty:
            tempsettings[each] = dicty[each]
        id_object.settings = repr(tempsettings)
        id_object.save()
        return True
    return False

def push_dataset_settings(dataset, settings):
    dataset.description = repr(settings)
    dataset.save()
