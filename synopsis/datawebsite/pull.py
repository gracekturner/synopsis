from django.db import models
from django.contrib.auth.models import User
from forms import *
from mapping import *

def string_to_boolean(string):
    if string:
        return True
    if not string:
        return False

# get id object from netid x7
def get_id(netid):
    if User_Settings.objects.filter(name = netid):
        return User_Settings.objects.filter(name = netid)[0]
    return False

def pull_tuples(dataset):
    rows = dataset.vector_set.all()
    tuples = {}
    for i in range(len(rows)):
        #NOTE make sure this is raw??
        #tuples[i] = eval(rows[i].raw_vector)
        tuples[i] = eval(rows[i].processed_vectors)
    return tuples

def pull_dataset(netid):
    id_object = get_id(netid)
    #print type(id_object)
    settings = pull_settings(netid)
    if id_object.datasets.filter(name = settings["dataset"]):
        dataset = id_object.datasets.filter(name = settings["dataset"])[0]
        tuples = pull_tuples(dataset)
        return tuples, dataset
    return False

# get id object settings from netid x4
def pull_settings(netid):
    id_object = get_id(netid)
    if id_object:
        return eval(id_object.settings)
    return False

def pull_column(tuples, i):
    column = []
    for each in tuples:
        column.append(tuples[each][i])
    return column

def pull_dataset_settings(dataset):
    return eval(dataset.description)

def pull_raw_dataset(dataset):
    rows = dataset.vector_set.all()
    tuples = {}
    for i in range(len(rows)):
        tuples[i] = eval(rows[i].raw_vector)
    return tuples

def pull_raw_column(dataset, i):
    tuples = pull_raw_dataset(dataset)
    return pull_column(tuples, i)

def pull_datasets(netid):
    id_object = get_id(netid)
    dictionary = {}
    for each in id_object.datasets.all():
        dictionary[each.name] = each.id
    return dictionary

def pull_processed_data(dataset,i, types):
    #dataset.property_set.all().delete()
    if dataset.property_set.filter(name = str(i) + "_" + str(types)):
        #make_cat(dataset, i, types)
        if types == "1":
            make_mc(dataset, i, types)
        return eval(dataset.property_set.filter(name = str(i) + "_" + str(types))[0].description)

    if True:
        if types == "1":
            #print "i get here??"
            prop = make_mc(dataset, i, types)
            return eval(prop.description)
        if types == "0":
            prop = make_cat(dataset, i, types)
            return eval(prop.description)

def make_mc(dataset, i, types):

    tuples = pull_tuples(dataset)
    full = pull_raw_column(dataset, i)

    keys = find_appropriate_mc(full, i)

    data = reduce_mapping_simple(keys, 2)
    mc = []
    for each in data:
        mc.append((each, data[each]))
    mc.sort(key=lambda tup: tup[1], reverse = True)
    alls = {}
    alls["reduced"] = mc
    alls["data"] = keys

    if dataset.property_set.filter(name = str(i) + "_" + str(types)):
        mc_prop = dataset.property_set.filter(name = str(i) + "_" + str(types))[0]
        mc_prop.description = repr(alls)
        mc_prop.save()
        return
    mc_prop = Property(name = str(i) + "_" + str(types), description = repr(alls), parent = dataset)
    mc_prop.save()
    return mc_prop

def make_cat(dataset, i, types):
    cat = {}
    cat["truth"] = []
    cat["view"] = "00"
    full = pull_column(pull_tuples(dataset), i)
    cat["all"] = {}
    for j in range(len(full)):
        cat["all"][j] = {}
    cat["upd"] = 0
    cat["choices"] = {}
    cat["frequency"] = {}
    if dataset.property_set.filter(name = str(i) + "_" + str(types)):
        cat_prop = dataset.property_set.filter(name = str(i) + "_" + str(types))[0]
        cat_prop.description = repr(cat)
        cat_prop.save()
    else:
        cat_prop =  Property(name = str(i) + "_" + str(types), description = repr(cat), parent = dataset)
        cat_prop.save()
    return cat_prop
