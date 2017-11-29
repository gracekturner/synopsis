# import shit
from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext as _
from django import forms
from models import *
import operator

# Options for Text Type
TEXT_TYPE_OPTIONS =  (
    (0, _("Text")),
    (1, _("Multiple Choice, Ranking, Etc.")),
    (2, _("Numeric")),
)

# options builder given dictionary, where the label is the key and
# the submitted value is the value in the dictionary.
#placeholder is what is displayed before clicking on select
#builtins are given the value "0" + the index of the builtin, while
# the label is builtin[value]
def options_builder(dictionary, placeholder = "", builtins = []):
    OPTIONS = ()
    if placeholder:
        action = ("", _(placeholder))
        OPTIONS += (action, )
    if builtins:
        count = 0
        for each in builtins:
            val = "0" +str(count)
            action = (val, _(each))
            OPTIONS += (action, )
            count+=1

    for each in dictionary:
        action = (str(dictionary[each]), _(each))
        OPTIONS += (action,)

    return OPTIONS


# form to display relationship between row and category
# for text processing
class TruthForm(forms.Form):
    def __init__(self,*args,**kwargs):
        #categories
        choices = kwargs.pop('extra')
        #column id, row id identifiers
        colid = kwargs.pop('colid')
        rowid = kwargs.pop('rowid')
        keys = kwargs.pop('choices')
        super(TruthForm,self).__init__(*args,**kwargs)

        self.fields["colid"] = forms.CharField(initial = colid, widget = forms.HiddenInput())
        self.fields["rowid"] = forms.CharField(initial = rowid, widget = forms.HiddenInput())
        self.fields["form_type"] = forms.CharField(initial = "TruthForm", label = "", widget = forms.HiddenInput())
        # for each in choices, if choices[each], display as selected etc.
        for each in choices:
            for key, value in keys.iteritems():
                if value == each:
                    if choices[each]:
                        self.fields['select_%s' % each] = forms.BooleanField(label= str(key), required = False, widget = forms.CheckboxInput(attrs = { "checked": "checked", "class": "delete-button"}))
                    else:
                        self.fields['select_%s' % each] = forms.BooleanField(label= str(key), required = False, widget = forms.CheckboxInput(attrs = {"class": "delete-button"}))

# compare two or more category forms.

class CrossTab(forms.Form):
    def __init__(self,*args,**kwargs):
        #categories
        choices = kwargs.pop('extra')
        super(CrossTab,self).__init__(*args,**kwargs)

        self.fields["row_view"] = forms.ChoiceField(label = "Change Row Category", required =False, choices = views, widget = forms.Select(attrs = {"onchange": "this.form.submit()", "class": "delete-button"}))
        self.fields["col_view"] = forms.ChoiceField(label = "Change Column Category", required =False, choices = views, widget = forms.Select(attrs = {"onchange": "this.form.submit()", "class": "delete-button"}))

#summary of category form. adds category, deletes category, and view displays
class CatForm(forms.Form):
    def __init__(self,*args,**kwargs):
        # category options
        choices = kwargs.pop('extra')
        #column id identifier
        colid = kwargs.pop('colid')
        #current frequencies for each category
        freq = kwargs.pop('freq')
        #display options
        views = options_builder(choices, placeholder = "Change Category View", builtins = ["All", "Uncategorized"])
        super(CatForm,self).__init__(*args,**kwargs)

        #add a choice
        self.fields["addchoice"] = forms.CharField(label = "Add Category", required = False, widget = forms.TextInput(attrs = {"onchange": "this.form.submit()"}) )
        #important information
        self.fields["colid"] = forms.CharField(initial = colid, label = "", widget = forms.HiddenInput())
        self.fields["form_type"] = forms.CharField(initial = "CatForm", label = "", widget = forms.HiddenInput())
        #display a certain filter
        self.fields["category_view"] = forms.ChoiceField(label = "Change Category View", required =False, choices = views, widget = forms.Select(attrs = {"onchange": "this.form.submit()", "class": "delete-button"}))
        #display each category + frequency value, sorted, with delete option
        freq = sorted(freq.items(), key=operator.itemgetter(1), reverse = True)
        for each in freq:
            for k, v in choices.iteritems():
                if v == each[0]:
                    self.fields['delete_%s' % v] = forms.BooleanField(label=  k + ": " + str(each[1]) + " Delete? ", required = False, widget = forms.CheckboxInput(attrs = {"onclick": "this.form.submit()", "class": "delete-button"}))


class DatasetForm(forms.Form):
    def __init__(self,*args,**kwargs):
        choices = kwargs.pop('extra')
        super(DatasetForm,self).__init__(*args,**kwargs)
        views = options_builder(choices, placeholder = "Change Dataset", builtins = [])
        self.fields["data_view"] = forms.ChoiceField(label = "Change Dataset", required =False, choices = views, widget = forms.Select(attrs = {"onchange": "this.form.submit()", "class": "delete-button"}))
        self.fields["form_type"] = forms.CharField(initial = "DatasetForm", label = "", widget = forms.HiddenInput())
class ColumnForm(forms.Form):
    #NOTE add id to col_type (? or one of them) for html css
    def __init__(self,*args,**kwargs):
        extra = kwargs.pop('extra')
        deleted = kwargs.pop('deleted')
        super(ColumnForm,self).__init__(*args,**kwargs)
        self.fields['col_type']= forms.CharField(widget = forms.HiddenInput(), label = "", initial = str(deleted), required = False)
        self.fields["form_type"] = forms.CharField(initial = "ColumnForm", label = "", widget = forms.HiddenInput())
        for i in range(len(extra)):
            if extra[i]["delete"] == deleted:

                if extra[i]["selected"]:
                    self.fields['column_%s' % i] = forms.BooleanField(label= extra[i]["name"], widget = forms.CheckboxInput(attrs = {"onclick": "this.form.submit()", 'class': 'column-button', 'checked':'checked'}))
                else:
                    self.fields['column_%s' % i] = forms.BooleanField(label= extra[i]["name"], widget = forms.CheckboxInput(attrs = {"onclick": "this.form.submit()", 'class': 'column-button'}))
                self.fields['type_%s' % i] = forms.ChoiceField(label = "", choices = TEXT_TYPE_OPTIONS, initial = extra[i]["type"], widget = forms.Select(attrs = {"onchange": "this.form.submit()", "class": "type-button"}))
                if deleted == False:
                    self.fields['delete_%s' % i] = forms.BooleanField(label= "Delete?", widget = forms.CheckboxInput(attrs = {"onclick": "this.form.submit()", "class": "delete-button"}))
                if deleted == True:
                    self.fields['reset_%s' % i] = forms.BooleanField(label= "Undo Delete?", widget = forms.CheckboxInput(attrs = {"onclick": "this.form.submit()","class": "delete-button"}))


# creates signup form
class UserForm(forms.Form):
    username = forms.CharField(label = "Username", required = True)
    password = forms.CharField(label = "Password", widget=forms.PasswordInput())
    password2 = forms.CharField(label = "Password", widget=forms.PasswordInput())

# creates login form
class Login(forms.Form):
    username = forms.CharField(label = "Username", required = True)
    password = forms.CharField(label = "Password", required = True, widget = forms.PasswordInput() )

# upload file chars
class UploadForm(forms.Form):
    #sheet_name = forms.CharField(label = "Excel Sheet Name",required=True,)
    form_type = forms.CharField(initial = "UploadForm", label = "", widget = forms.HiddenInput())
    dataset_title = forms.CharField(required=True)
    File = forms.FileField(required = True)
