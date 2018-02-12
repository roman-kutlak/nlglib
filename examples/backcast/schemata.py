"""This module defines schemata for answering communicative goals

A schema is essentially a group of messages.

"""

from nlglib.macroplanning import RhetRel

from . import messages


class Schema:
    """A schema contains a document plan of rhetorical relations"""

    attributes = [
        ('mean_temperature', 'deg_celsius'),
        ('minimum_temperature', 'deg_celsius'),
        ('maximum_temperature', 'deg_celsius'),
        ('sunshine', 'hour'),
        ('rain_days', 'day')
    ]

    def __init__(self, kb=None):
        self.kb = kb
        self.document_plan = None

    def instantiate(self, kb):
        """Instantiate the schema"""
        pass


class DescribeYear(Schema):
    """Describe the weather of a given year"""

    def __init__(self, year, kb=None):
        super().__init__(kb)
        self.year = year
        if kb:
            self.instantiate(kb)

    def instantiate(self, kb):
        """Instantiate the schema"""
        selected_messages = []
        year = kb[self.year]
        for attribute, unit in self.attributes:
            value = getattr(year, attribute, None)
            if value:
                template_name = 'report-temperature' if unit in ('deg_celsius', ) else 'report-duration'
                report_value = messages.ReportValue(self.year, attribute, value,
                                                    units=unit, template_name=template_name)
                selected_messages.append(report_value)
        self.document_plan = RhetRel('sequence', *selected_messages)
