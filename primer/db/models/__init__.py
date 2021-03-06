from django.db import models

from fields import UUIDField, PickleField

##################################################################################################################
# Custom Abstract Base Models
##################################################################################################################
class PrimerModel(models.Model):
    """
    Primer model adds the following fields to a model
    - created
    - modified
    - UUID
    """
    class Meta:
        abstract = True
        get_latest_by = 'created'
    
    created = models.DateTimeField(auto_now_add=True, editable = False, blank = True, null = True)
    modified = models.DateTimeField(auto_now=True, blank = True, null = True)
    uuid = UUIDField()