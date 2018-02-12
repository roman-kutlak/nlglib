"""This module specifies what kind of messages the system can produce

Each message roughly corresponds to a clause. An example message
might be a structure that represents "no data"
and gets eventually realised as "There is no data for February 2110".

"""

from nlglib.macroplanning import RhetRel, MsgSpec, StringMsg, PredicateMsg
from nlglib.microplanning import NP, String


class NoData(MsgSpec):
    """Tell the user that there is no data"""

    def __init__(self, year, month=None):
        super().__init__('no-data')
        self.year = year
        self.month = month

    @property
    def date(self):
        """Return the date expression"""
        if self.month:
            return NP('{0} {1}'.format(self.month, self.year))
        else:
            return NP(self.year)


class DontUnderstand(MsgSpec):
    """Tell the user that the system doesn't understand the communicative goal"""

    def __init__(self, goal):
        super().__init__('do-not-understand')
        self.goal = goal


class ReportValue(MsgSpec):
    """Report a value of an attribute"""

    def __init__(self, year, attribute, value, units=None, template_name='report-value'):
        super().__init__(template_name)
        self.year = year
        self.attribute = attribute
        self.value = value
        self._units = units

    @property
    def units(self):
        if self.value != 1.0:
            return String(self._units, features={'NUMBER': 'plural'})
