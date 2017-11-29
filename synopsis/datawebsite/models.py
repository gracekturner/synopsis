from __future__ import unicode_literals

from django.db import models

# individual row of data. has parent(s) dataset(s)
class Vector(models.Model):
    # raw row saved (does not get edited!)
    raw_vector = models.TextField()
    # processed row(s) if multi select e.g., than multiple rows (whatever the current version of the mapping)
    processed_vectors = models.TextField()
    # the dataset(s) associated with the vector
    parent = models.ForeignKey("Property", on_delete=models.CASCADE, null = True)

# includes dataset title, any processed stuff that needs saving
# can associate with itself
class Property(models.Model):
    # name (e.g. "Dataset_" + name or "Freq_" + columnname)
    name = models.CharField(max_length = 200, null = True)
    # usually an eval, depends on the type of property
    description = models.TextField()
    #parent property (e.g. a frequency reduction of a dataset's parent would be the dataset property)
    parent = models.ForeignKey("Property", on_delete=models.CASCADE, null = True)

#user settings. does not include login info.
class User_Settings(models.Model):
    #username
    name = models.CharField(max_length = 200)
    # settings, including workspace settings
    settings = models.TextField()
    # associated datasets
    datasets = models.ManyToManyField(Property)
