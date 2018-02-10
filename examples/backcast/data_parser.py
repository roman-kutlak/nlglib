"""Parse the weather data in a given folder and return a dict with YearData instances"""

import math
import re
import os

months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

seasons = ['WIN', 'SPR', 'SUM', 'AUT']

other = ['ANN']

columns = [
    'Year',
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
    'WIN', 'SPR', 'SUM', 'AUT',
    'ANN'
]


def parse_data(folder):
    data = {}
    for file in os.listdir(folder):
        filename, _, ext = file.rpartition('.')
        # the file name is also the attribute (eg mean_temperature)
        attribute = filename
        if ext != 'txt':
            continue
        with open(os.path.join(folder, file), 'r') as fd:
            for line in fd:
                if not starts_with_year(line):
                    continue
                else:
                    line_tokens = [x.strip() for x in line.split(' ') if x.strip()]
                    line_data = dict(zip(columns, line_tokens))
                    try:
                        year = int(line_data.pop('Year'))
                    except:
                        continue
                    year_data = data.setdefault(year, YearData(year))
                    def consume_value(key):
                        try:
                            return float(line_data.pop(key))
                        except:
                            return None
                    # set the annual average
                    avg = consume_value('ANN')
                    setattr(year_data, attribute, avg)
                    # we are left with months and seasons
                    for s in seasons:
                        season_data = year_data.seasons[s]
                        setattr(season_data, attribute, consume_value(s))
                    for m in months:
                        month_data = year_data.months[m]
                        setattr(month_data, attribute, consume_value(m))
    return data


class WeatherData:
    """Class for holding weather data"""

    # help autocomplete
    airfrost_days = None
    maximum_temperature = None
    mean_temperature = None
    minimum_temperature = None
    rain_days = None
    rainfall = None
    sunshine = None

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    def __str__(self):
        keys = sorted([k for k in self.__dict__.keys() if not k.startswith('_')])
        return ', '.join('{0}-{1}'.format(k, self.__dict__[k]) for k in keys)

    def update(self, **attrs):
        self.__dict__.update(**attrs)


class YearData(WeatherData):
    """Class for holding data about a given year

    Aside from data for individual seasons/months,
    year also has average data point for the year.

    """

    def __init__(self, year, **kwargs):
        super().__init__(**kwargs)
        self.year = int(year)
        self.seasons = {s: SeasonData(self, s) for s in seasons}
        self.months = {m: MonthData(self, m) for m in months}

    def __str__(self):
        return str(self.year)

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.year)


class SeasonData(WeatherData):
    """Class for holding weather data about a given season"""

    def __init__(self, year, season, **kwargs):
        super().__init__(**kwargs)
        self.year = year
        self.season = season

    def __str__(self):
        return '{0}: {1}'.format(self.year, self.season)

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, str(self))


class MonthData(WeatherData):
    """Class for holding weather data about a given month"""

    def __init__(self, year, month, **kwargs):
        super().__init__(**kwargs)
        self.year = year
        self.month = month

    def __str__(self):
        return '{0}-{1}'.format(self.year, self.month)

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, str(self))


class SummaryStats:
    """Summary statistics of a data stream (eg mean_temperature)"""

    mean = None
    std_dev = None
    min_value = None
    max_value = None

    def __init__(self, data):
        self.process(data)

    def process(self, data):
        if not data:
            return
        self.mean = sum(data) / float(len(data))
        self.min_value = min(data)
        self.max_value = max(data)
        if len(data) > 1:
            self.std_dev = math.sqrt(sum((x - self.mean)**2 for x in data) /
                                     float(len(data) - 1))


def starts_with_year(s, pattern=re.compile('\d{4}\s.*')):
    return bool(pattern.match(s))
