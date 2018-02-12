"""This module provides templates for lexicalisation"""

from nlglib.features import NEGATED, TENSE
from nlglib.microplanning import *


def report_value_fn(msg, templates, **kwargs):
    """Return template X is V based on whether units are specified"""
    rv = Clause(Var('attribute'), VP('is', Var('value'), features=[TENSE.past]))
    rv.predicate.premodifiers.append(PP('in', Var('year')))
    if msg.units:
        rv.predicate.complements.append(Var('units'))
    return rv


def report_duration_fn(msg, templates, **kwargs):
    """Return template X has V based on whether units are specified"""
    rv = Clause(Var('year'), VP('has', Var('value'), features=[TENSE.past]))
    if msg.units:
        rv.predicate.complements.append(Var('units'))
    rv.predicate.complements.append(PP('of', Var('attribute')))
    return rv


templates = {
    'no-data': Clause('there', VP('be', NP('no', 'data'), PP('for', Var('date')))),
    'do-not-understand': Clause('I', VP('understand', NP('the', 'goal'), Var('goal'), features=[NEGATED.true])),
    'report-value': report_value_fn,
    'report-temperature': report_value_fn,
    'report-duration': report_duration_fn,
    # attribute names and units
    'mean_temperature': NP('the', 'mean', 'temperature'),
    'minimum_temperature': NP('the', 'mean', 'minimum', 'temperature'),
    'maximum_temperature': NP('the', 'mean', 'maximum', 'temperature'),
    'rain_days': NP('rain', 'days'),
    'airfrost_days': NP('airfrost', 'days'),
    'sunshine': NP('sunshine'),
    'rainfall': NP('rain fall'),
    'deg_celsius': NP('degree', postmodifiers=['Celsius']),
    'deg_centigrade': NP('degree', postmodifiers=['Centigrade']),
    'hour': NP('hour'),
    'day': NP('day'),
}
