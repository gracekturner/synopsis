from push import *
from pull import *
from mapping import *
import pandas

def parse_column_form(request, netid):
    #find the differences
    tuples, dataset = pull_dataset(netid)
    columns = pull_dataset_settings(dataset)
    changes = []

    for i in range(len(columns)):

        # get settings back
        column = string_to_boolean(request.POST.get('column_' + str(i), ""))
        types = request.POST.get('type_' + str(i), "")
        delete = string_to_boolean(request.POST.get('delete_'+str(i), ""))
        reset = string_to_boolean(request.POST.get('reset_'+str(i), ""))

        #if they don't match, append
        if column != columns[i]["selected"]:
            changes.append((i, "selected", column))

        if types != columns[i]["type"]:
            changes.append((i, "type", types))

        if delete:
            changes.append((i, "delete", delete))
        if reset:
            changes.append((i, "delete", False))

    # for each in changes
    for each in changes:
        if each[1] == "selected":
            for sett in columns:
                sett["selected"] = False
        columns[each[0]][each[1]]= each[2]
    # save changes
    push_dataset_settings(dataset, columns)



def parse_dataset_form(request, netid, val):
    id_object = get_id(netid)
    data_obj = id_object.datasets.filter(id = val["data_view"])
    if data_obj:
        data_obj = data_obj[0]
        dicty = {}
        dicty["dataset"] = data_obj.name
        dicty["data_length"] = len(data_obj.vector_set.all())
        push_settings(netid, dicty)



def estimate_columns(data, pandastype):
    settings = {}

    count = 0
    for k, v in data.iteritems():
        if pandastype[k] == "datetime64[ns]":
            settings[k] = "3"
            continue

        vals = find_appropriate_mc(v, k)
        data = reduce_mapping_simple(vals, 2)
        #print len(vals
        if len(data) < 15:
            settings[k] = "1"
        else:
            settings[k] = "0"
    return settings



def parse_post_file(request, netid):
    # get file information
    dataset = request.POST.get('dataset_title', '')
    excel = request.FILES['File']
    #NOTE make sure to check that file is an excel xlsx
    #NOTE get dataset from the first sheet (will expand further later)
    data = pandas.read_excel(excel, sheetname = 0)
    data = data.where((pandas.notnull(data)), "")
    if data.empty: return dataset

    da = data.dtypes
    print data.dtypes
    g = data.columns.to_series().groupby(data.dtypes).groups
    g = {k.name: v for k, v in g.items()}
    #print g
    if 'datetime64[ns]' in g:
         tofix = g['datetime64[ns]']
         for each in tofix:
            data[each] = data[each].dt.strftime('%d-%m-%Y, %H:%M:%S')
    d = data.to_dict(orient = 'list')
    estimates = estimate_columns(d, da)
    


    #create a Property dataset
    #listy = zip(data, estimates)
    columns = []

    for each in list(data):
        columns.append({"name": each, "type": estimates[each], "delete": False, "processed": False, "selected": False})

    data_property = Property(name = dataset, description = repr(columns))
    data_property.save()
    id_object = get_id(netid)
    id_object.datasets.add(data_property)

    #create Property vectors
    data = data.to_dict('split')
    for each in data["data"]:

        v = Vector(raw_vector = repr(each), processed_vectors = repr(each), parent = data_property)
        v.save()

    #update id object settings
    dicty = {}
    dicty["dataset"]= dataset
    dicty["data_length"] = len(data["data"])
    settings = push_settings(netid, dicty)





def parse_truth_form(request, dataset, settings, val):
    i = int(val['colid'])
    j = int(val['rowid'])
    cat_prop = pull_processed_data(dataset, i, "0")
        #cat_prop["frequency"] = {}
    column = pull_raw_column(dataset, i)
    for each in cat_prop["choices"]:
        choice = request.POST.get('select_'+str(cat_prop["choices"][each]), "")
            #print choice, string_to_boolean(choice)
        cat_prop["all"][j][cat_prop["choices"][each]] = string_to_boolean(choice)
        if choice:
            test = basic_learning_algorithm(cat_prop["choices"][each], column[j], column, 0.1)
            for t in test:
                cat_prop["all"][t[1]][t[0]] = True
                cat_prop["frequency"][t[0]] +=1
        else:
            test = basic_learning_algorithm(cat_prop["choices"][each], column[j], column, 0.8)

            for t in test:
                cat_prop["all"][t[1]][t[0]] = False
                cat_prop["frequency"][t[0]] -=1
    push_processed_data(dataset, i, "0", cat_prop)


def parse_category_form(request, dataset, settings, val):
    i = int(val['colid'])
    types = settings[i]["type"]
    cat_prop = pull_processed_data(dataset, i, types)
    add = val["addchoice"]
    if val['category_view']:
        cat_prop["view"] = val['category_view']
    if val['addchoice']:
        cat_prop["choices"][add] = cat_prop["upd"]
        cat_prop["frequency"][cat_prop["upd"]] = 0
        for each in cat_prop["all"]:
            cat_prop["all"][each][cat_prop["upd"]] = False
        cat_prop["upd"] +=1
    # get deleted
    newchoices = {}
    newfrequencies = {}
    for k, v in cat_prop["choices"].iteritems():
        if not request.POST.get('delete_' + str(v), ""):
            newchoices[k] = v
            newfrequencies[v] = cat_prop["frequency"][v]

        else:
            for row in cat_prop["all"]:
                cat_prop["all"][row][v] = None


                #will need to do something here to remove truth/all
    cat_prop["choices"] = newchoices
    cat_prop["frequency"] = newfrequencies

    push_processed_data(dataset, i, types, cat_prop)
