"""This module provides simple means for specifying communicative goals"""


class Describe:
    """Ask the system to create a description of something (year/month)"""

    def __str__(self):
        return self.__class__.__name__


class Compare:
    """Ask the system to compare two or more items (years/months)"""

    def __str__(self):
        return self.__class__.__name__


class DescribeYear(Describe):
    """Describe given year"""
    def __init__(self, year):
        self.year = year


class DescribeMonth(Describe):
    """Describe given month of a given year"""
    def __init__(self, year, month):
        self.year = year
        self.month = month

