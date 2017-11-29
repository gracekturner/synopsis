from nltk import word_tokenize
from decimal import *
from django.db import models
#from pandas import pd

def mappings_to_dataset(mappings, dataset, tuples):
    prevrow = 0

    for each in mappings:
        row = each[0]
        col = each[1]
        if type(tuples[row][col]) != list:
            tuples[row][col] = []
            tuples[row][col].append(each[2])
        else:
            tuples[row][col].append(each[2])
    #push_dataset(dataset, tuples)
    return tuples
def dict_to_mappings(dicty):
    mapping = []
    for each in dicty:
        mapping.append((each, dicty[each]))
    return mapping

def value_to_mappings(tuples, col_id, row_id, mapping):

    value = tuples[row_id][col_id]
    if type(value) is list:
        for each in value:
            mapping.append((row_id, col_id, each))
    else:
        mapping.append((row_id, col_id, value))
    return mapping

def dataset_to_mappings(dataset, tuples, column_index = ""):
    mapping = []
    if not column_index:
        for row in range(len(tuples)):
            for c in range(len(tuples[row])):
                mapping = value_to_mappings(tuples, c, row, mapping)

    else:
        if type(column_index) == int:

            for row in range(len(tuples)):
                mapping = value_to_mappings(tuples, column_index, row, mapping)
        else:
            for c in column_index:
                for row in range(len(tuples)):
                    mapping = value_to_mappings(tuples, c, row, mapping)

    return mapping

def frequency_table_creator(dataset, tuples, column_index):
    mappings = dataset_to_mappings(dataset, tuples, column_index)
    return reduce_mapping_simple(mappings, 2)

def reduce_mapping_simple(mappings, tuple_index):
    dicty = {}

    for each in mappings:
        if not each[tuple_index]:
            continue
        if each[tuple_index] not in dicty:
            dicty[each[tuple_index]] = 0
        dicty[each[tuple_index]] += 1
    return dicty


def reduce_mapping_complex(mappings, tuple_indexes):
    df = pd.DataFrame(mappings)
    print df

def similarity_opt(pair):
    one = pair[0]
    two  = pair[1]

    inter = one.intersection(two)
    uni = one.union(two)
    if len(uni) == 0:
        return 1
    return Decimal(len(inter))/(Decimal(len(uni)))

def lower_tokenize(text):
    text = word_tokenize(text)
    test = []
    for word in text:
        if word in [".", ",", "!", "?", "&", "/", "and", "", "to", "the", "a"]:
            continue
        test.append(word.lower())
    return test

def basic_learning_algorithm(category, text, column, threshold):
    if type(text) == int:
        text = str(text)
    if type(text) == bool:
        text = str(text)
    test = set(lower_tokenize(text))
    newcol = []
    for i in range(len(column)):
        words = column[i]
        if type(words) == int:
            words = str(words)
        if type(words) == bool:
            words = str(words)
        words = set(lower_tokenize(words))
        if similarity_opt([test, words]) > threshold:
            newcol.append((category, i))
    return newcol
    #keys = map_text_to_tokens(column, column_index)
    #reduce_mapping_complex(keys, [])



def map_text_to_tokens(column, column_index):
    keys = []
    for i in range(len(column)):
        words = column[i]
        if type(words) == int:
            words = str(words)
        if type(words) == bool:
            words = str(words)
        words = word_tokenize(words)
        for word in words:

            if word in [".", ",", "!", "?", "&", "/", "and", ""]:
                continue
            if not word:
                continue
            keys.append((i, column_index, word.lower()))
    return keys

def map_text_to_splits(column, column_index, regex):
    keys = []
    for i in range(len(column)):
        words = column[i]
        if type(words) == int:
            words = str(words)
        if type(words) == bool:
            words = str(words)
        words = words.lower()
        words = words.strip()
        print words
        words = words.split(regex)
        #words = words.lower()

        for word in words:
            keys.append((i, column_index, word))
    return keys

def find_appropriate_mc(column, column_index):
    # try word tokens
    keys = map_text_to_tokens(column, column_index)
    red = reduce_mapping_simple(keys, 2)
    #print "tokens: ", keys, red, len(red)
    # try csv
    keys2 = map_text_to_splits(column, column_index, ",")
    red2 = reduce_mapping_simple(keys2, 2)

    # try plain
    keys3 = map_text_to_splits(column, column_index, "\n")
    red3 = reduce_mapping_simple(keys3, 2)


    #print "sentences: ", keys2, red2, len(red2)
    alls = [("1", len(red)), ("2", len(red2)), ("3", len(red3))]
    alls.sort(key=lambda tup: tup[1])
    returns = alls[0]
    if returns[0] == "1":
        return keys
    if returns[0] == "2":
        return keys2
    if returns[0] == "3":
        return keys3
