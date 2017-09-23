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
this set up an application context with pipeline.pipeline_context().  See the
documentation for more information.\
'''

_lexicon_ctx_err_msg = '''\
Working outside of lexicon context.

This typically means that you attempted to use functionality that needed
to interface with the current application object in a way.  To solve
this set up an application context with pipeline.lexicon_context().  See the
documentation for more information.\
'''

_linguistic_ctx_err_msg = '''\
Working outside of linguistic context.

This typically means that you attempted to use functionality that needed
to interface with the current application object in a way.  To solve
this set up an application context with pipeline.linguistic_context().  See the
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


def _find_lexicon():
    top = _lexicon_ctx_stack.top
    if top is None:
        raise RuntimeError(_lexicon_ctx_err_msg)
    return top.lexicon


def _find_linguistic_context():
    top = _linguistic_ctx_stack.top
    if top is None:
        raise RuntimeError(_linguistic_ctx_err_msg)
    return top


# context locals
_lexicon_ctx_stack = LocalStack()
_pipeline_ctx_stack = LocalStack()
_linguistic_ctx_stack = LocalStack()
current_lexicon = LocalProxy(_find_lexicon)
current_pipeline = LocalProxy(_find_pipeline)
current_linguistic_context = LocalProxy(_find_linguistic_context)
lexicon = LocalProxy(partial(_lookup_pipeline_object, 'lexicon'))
g = LocalProxy(partial(_lookup_pipeline_object, 'g'))
