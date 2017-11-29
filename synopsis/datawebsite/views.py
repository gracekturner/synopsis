from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.db import models
from forms import *
from django.contrib.auth.models import User
import pandas
from mapping import *
import StringIO
import xlsxwriter
import operator
from push import *
from pull import *
from formspush import *

#logout
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    # Take the user back to the homepage.
    return redirect('homepage')

#def parse_post_workspace(request, netid):
    # check if changes happen to dataset, update, return
    extras = pull_datasets(netid)
    form = DatasetForm(request.POST, extra = extras)
    dataset = request.POST.get('data_view', '')
    if dataset:
        id_object = get_id(netid)

        data_obj = id_object.datasets.filter(id = dataset)
        if data_obj:
            data_obj = data_obj[0]
            dicty = {}
            dicty["dataset"] = data_obj.name
            dicty["data_length"] = len(data_obj.vector_set.all())
            push_settings(netid, dicty)
            return


    tuples, dataset = pull_dataset(netid)
    settings = pull_dataset_settings(dataset)

    # get setting changes
    changes = make_settings_change(request, netid)

    for each in changes:
        if each[1] == "selected":
            for sett in settings:
                sett["selected"] = False
        settings[each[0]][each[1]]= each[2]
    # save changes
    push_dataset_settings(dataset, settings)


    #make active changes
    make_active_change(request, netid, settings)


    #look at changes in selection
    #make_selection_change(request, netid, settings)

def check_for_val(request, strings, name):
    values = {}
    # check if the form is valid
    formtype = request.POST.get("form_type", '')

    if formtype != name:
        #print "i get here ", formtype, name
        return False
    # else
    for s in strings:
        values[s] = request.POST.get(s, '')

    return values

def push_workspace(request, netid):
    # update category settings
    # if first time
    if pull_dataset(netid):
        _, dataset = pull_dataset(netid)
    else:
        parse_post_file(request, netid)
        return
    # get dataset settings
    settings = pull_dataset_settings(dataset)
    # for each possible form
    allforms = {}
    allforms["CatForm"] = ['colid', 'category_view', 'addchoice']
    allforms["DatasetForm"] = ['data_view']
    allforms["ColumnForm"] = ["col_type"]
    allforms["TruthForm"] = ['colid', 'rowid']
    allforms["UploadForm"] = ['dataset_title']

    for each in allforms:
        val = check_for_val(request,  allforms[each], each)
        if not val:
            continue
        if each == "CatForm":
            parse_category_form(request, dataset, settings, val)
        if each == "TruthForm":
            parse_truth_form(request, dataset, settings, val)
        if each == "UploadForm":
            parse_post_file(request, netid)
        if each == "ColumnForm":
            parse_column_form(request, netid)
        if each == "DatasetForm":
            parse_dataset_form(request, netid, val)
        # NOTE FINISH THIS!







def get_results(choices, full, view, i):
    alls = []
    results = []

    for j in range(len(choices["all"])):
        # if view == "00" (eg.) all categorization statuses
        if view == "00":
            if len(choices["choices"]) > 0:
                alls.append(TruthForm(colid = i, rowid = j, extra = choices["all"][j], choices = choices["choices"]))
            continue
        # if view == "01" only uncategorized
        if view == "01":
            test = True
            for each in choices["all"][j]:
                if choices["all"][j][each]:
                    test = False
            if test:
                if len(choices["all"][j]) > 0:
                    results.append((j, full[j],
                        TruthForm(colid = i, rowid = j, extra = choices["all"][j], choices = choices["choices"])))
                else:
                    results.append((j, full[j]))
            continue
        # else: the specific option created by the user
        ch = int(view)
        if choices["all"][j][ch]:
            results.append((j, full[j],TruthForm(colid = i, rowid = j, extra = choices["all"][j], choices = choices["choices"])))

    #because I was a little lazy
    if view == "00":

        if alls:
            results = zip(range(len(full)), full, alls)
        else:
            results = zip(range(len(full)), full)
    #print results
    return results


def pull_workspace(request, netid):
    templates = {}
    results = ""
    tuples, dataset = pull_dataset(netid)
    settings = pull_dataset_settings(dataset)
    for i in range(len(settings)):

        if settings[i]["selected"]:

            templates["selected_name"] = settings[i]["name"]
            results = pull_processed_data(dataset, i, settings[i]["type"])
            if settings[i]["type"] == "1":
                results = results["reduced"]

            if settings[i]["type"] == "0":
                #print "i:", i
                full = pull_raw_column(dataset, i)
                choices = pull_processed_data(dataset, i, settings[i]["type"])

                choices["frequency"] = {}
                for k, v in choices["choices"].iteritems():
                    choices["frequency"][v] = 0
                    for a in choices["all"]:
                        if choices["all"][a][v]:
                            choices["frequency"][v] = choices["frequency"][v] + 1

                freq = choices["frequency"]
                push_processed_data(dataset, i, settings[i]["type"], choices)
                if "view" in results:
                    results = get_results(results, full, results["view"], i)

                templates["selected_id"] = "0"

                templates["selected_choices"] = CatForm(extra = choices["choices"], freq = freq, colid = i)


    templates["selected_data"] = results
    return templates



def isfloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


# takes a dataset default: {sheet_name: {array_of_columns[]}}
# "a_o_t": {sheet_name: [array_of_tuples]} tuples: [i, j, val]
def WriteToExcel(dataset, types = "a_o_c"):
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)
    count = 0
    for each in dataset:

        ws = workbook.add_worksheet("Sheet_" + str(count))
        count +=1
        if types == "a_o_c":
            for i in range(len(dataset[each])):
                for j in range(len(dataset[each][i])):
                    ws.write(i, j, dataset[each][i][j])
        if types == "a_o_t":
            #print dataset[each]

            for t in dataset[each]:
                #print t
                ws.write(t[0], t[1], t[2])
        if types == "a_o_t2":
            for i in range(1, len(dataset[each])+1):
                for j in range(len(dataset[each][i-1])):
                    ws.write(i, j, dataset[each][i-1][j])
            ws.write(0, 0, each)

    workbook.close()
    xlsx_data = output.getvalue()
    # xlsx_data contains the Excel file
    return xlsx_data



def download2(request, netid):
    download2(request, netid)
    tuples, dataset = pull_dataset(netid)
    #print dataset_to_mappings(dataset, tuples)
    settings = pull_dataset_settings(dataset)
    excel = {}

    all_ids = []
    mc_ids = []
    cat_ids = []
    for each in range(len(settings)):

        if not settings[each]["delete"]:
            all_ids.append(each)
            if settings[each]["type"] == "1":
                mc_ids.append(each)
            if settings[each]["type"] == "0":
                cat_ids.append(each)
            #dataset_to_mappings(dataset, tuples, each)
            #column = pull_column(tuples, each)
            #column.insert(0, settings[each]["name"])
            #excel[dataset.name]= [column] + excel[dataset.name]
            #if settings[each]["type"] == "1":
                #column = dataset_to_mappings(dataset, tuples, each)
                #reduced = dict_to_mappings(reduce_mapping_simple(column, 2))
                #excel[settings[each]["name"]] = reduced
    excel[dataset.name] = dataset_to_mappings(dataset, tuples, all_ids)

    excel = WriteToExcel(excel, types = "a_o_t2")
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Report.xlsx'
    response.write(excel)
    return response


def download(request, netid):
    tuples, dataset = pull_dataset(netid)
    #print dataset_to_mappings(dataset, tuples)
    settings = pull_dataset_settings(dataset)
    excel = {}

    all_ids = []
    mc_ids = []
    cat_ids = []
    for each in range(len(settings)):

        if not settings[each]["delete"]:
            data = pull_processed_data(dataset, each, settings[each]["type"])

            if settings[each]["type"] == "1":
                #print data
                excel[settings[each]["name"]] = data['reduced']
            if settings[each]["type"] == "0":
                freq = data["frequency"]
                choices = data["choices"]
                opt = []
                if freq:
                    for each in freq:
                        for c in choices:
                            if choices[c] == each:
                                opt.append((c, freq[each]))
                    excel[settings[each]["name"]] = opt


            #print data
    #excel[dataset.name] = dataset_to_mappings(dataset, tuples, all_ids)

    excel = WriteToExcel(excel, types = "a_o_t2")
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename='+dataset.name + ".xlsx"
    response.write(excel)
    return response





#def make_settings_change(request, netid):
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
    return changes

def main(request, netid):
    #return dataset
    templates = {}
    results = ""
    sett = {}
    if request.method == 'POST':
        print "i get here"
        #form = UploadForm(request.POST)
        push_workspace(request, netid)

    #get settings for netid
    settings = pull_settings(netid)



    if settings["dataset"] == "":
        templates["dataset_name"] = "No Dataset Set to Default"
        templates["dataset_entries"] = "None"

    else:
        _, dataset = pull_dataset(netid)
        columns = pull_dataset_settings(dataset)
        templates = pull_workspace(request, netid)
        templates["dataset_columns"] = ColumnForm(extra = columns, deleted = False)
        templates["deleted_dataset_columns"] = ColumnForm(extra = columns, deleted = True)
        templates["dataset_name"] = settings["dataset"]
        templates["dataset_entries"] = str(settings["data_length"])
        templates["column_type_form"] = TEXT_TYPE_OPTIONS

    templates["upload_dataset_form"] = UploadForm()
    alldatasets = pull_datasets(netid)
    templates["old_dataset_form"] = DatasetForm(extra = alldatasets)
    templates["netid"] = netid

    return render(request, 'datawebsite/workspace.html', templates)

def main2(request, netid):
    #return dataset
    templates = {}
    results = ""
    sett = {}
    if request.method == 'POST':
        #form = UploadForm(request.POST)
        if request.POST.get('dataset_title', ""):
            parse_post_file(request, netid)
        else:
            parse_post_workspace(request, netid)

    #get settings for netid
    settings = pull_settings(netid)



    if settings["dataset"] == "":
        templates["dataset_name"] = "No Dataset Set to Default"
        templates["dataset_entries"] = "None"

    else:
        _, dataset = pull_dataset(netid)
        columns = pull_dataset_settings(dataset)
        templates = pull_workspace(request, netid)


        templates["dataset_columns"] = ColumnForm(extra = columns, deleted = False)
        templates["deleted_dataset_columns"] = ColumnForm(extra = columns, deleted = True)
        templates["dataset_name"] = settings["dataset"]
        templates["dataset_entries"] = str(settings["data_length"])
        templates["column_type_form"] = TEXT_TYPE_OPTIONS
    templates["upload_dataset_form"] = UploadForm()
    alldatasets = pull_datasets(netid)
    templates["old_dataset_form"] = DatasetForm(extra = alldatasets)
    templates["netid"] = netid

    return render(request, 'datawebsite/workspace.html', templates)


# login from homepage
def homepage_login(request):
    user_form = UserForm(request.POST)
    if user_form.is_valid():
        name = request.POST.get('username', '')
        psw = request.POST.get('password', '')
        if User.objects.filter(username=name).exists():
            return HttpResponse("This Username is already taken.")
        #create user profile
        user = User(username = name)
        user.set_password(psw)
        user.save()
        #create user_settings profile
        settings = repr({"dataset": ""})
        user = User_Settings(name = name, settings = settings)
        user.save()
    user_form = Login(request.POST)
    if user_form.is_valid():
        name = request.POST.get('username', '')
        psw = request.POST.get('password', '')
        user = authenticate(username = name, password = psw)
        if user is None:
            return HttpResponse("Your login or password is incorrect.")
    login(request, user)
    return redirect('main', netid=  name)


# homepage blank slate
def homepage(request):
    #if method == POST
    templates = {}
    templates['signup'] =  UserForm()
    templates['login'] = Login()
    if request.method == 'POST':
        return homepage_login(request)

    return render(request, 'datawebsite/homepage.html', templates)
