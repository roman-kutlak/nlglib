"""This module contains the backcast NLG system"""

import os

from nlglib.aggregation import SentenceAggregator
from nlglib.lexicalisation import Lexicaliser
from nlglib.realisation.simplenlg import Realiser

from .templates import templates
from .data_parser import parse_data
from . import messages
from . import goals


class BackCast:
    realiser = Realiser(host='nlg.kutlak.info')
    lexicaliser = Lexicaliser(templates=templates)
    aggregator = SentenceAggregator()

    def __init__(self, data_path=None):
        if not data_path:
            cwd = os.path.dirname(__file__)
            data_path = os.path.join(cwd, 'data')
        self.kb = parse_data(data_path)

    def communicate(self, goal, context=None, user_model=None, kb=None):
        """Take a given communicative goal and create appropriate response
        given the knowledge base, context and a user model.

        """
        kb = kb or self.kb
        if isinstance(goal, goals.DescribeYear):
            rv = self.describe_year(goal)
        elif isinstance(goal, goals.DescribeMonth):
            rv = self.describe_month(goal)
        else:
            rv = messages.DontUnderstand(goal)
        return self.verbalise(rv)

    def describe_month(self, goal):
        return messages.NoData(goal.year, goal.month)

    def describe_year(self, goal):
        return messages.NoData(goal.year)

    def verbalise(self, msg):
        lexicalised = self.lexicaliser(msg)
        aggregated = self.aggregator(lexicalised)
        realised = self.realiser(aggregated)
        return realised
