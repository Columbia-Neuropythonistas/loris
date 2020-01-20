"""Anatomy Tables
"""

import datajoint as dj
from loris.database.schema.base import ManualLookup

schema = dj.schema('anatomy')


@schema
class NeuronSection(ManualLookup, dj.Manual):
    primary_comment = 'section of a neuron - e.g. dendrite, soma'


@schema
class BrainArea(ManualLookup, dj.Manual):
    primary_comment = 'brain area - e.g. medulla'
