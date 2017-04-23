# -*- coding: utf-8 -*-
"""
    nlglib.globals
    ~~~~~~~~~~~~~~

    Defines all the global objects that are proxies to the current
    active context.

    :copyright: (c) 2015 by Armin Ronacher, (c) 2017 by Roman Kutlak
    :license: BSD, see LICENSE for more details.
"""

from functools import partial
from werkzeug.local import LocalStack, LocalProxy


_pipeline_ctx_err_msg = '''\
Working outside of pipeline context.

This typically means that you attempted to use functionality that needed
to interface with the current application object in a way.  To solve
this set up an application context with app.pipeline_context().  See the
documentation for more information.\
'''


def _lookup_pipeline_object(name):
    top = _pipeline_ctx_stack.top
    if top is None:
        raise RuntimeError(_pipeline_ctx_err_msg)
    return getattr(top, name)


def _find_pipeline():
    top = _pipeline_ctx_stack.top
    if top is None:
        raise RuntimeError(_pipeline_ctx_err_msg)
    return top.pipeline


# context locals
_pipeline_ctx_stack = LocalStack()
current_pipeline = LocalProxy(_find_pipeline)
lexicon = LocalProxy(partial(_lookup_pipeline_object, 'lexicon'))
g = LocalProxy(partial(_lookup_pipeline_object, 'g'))
