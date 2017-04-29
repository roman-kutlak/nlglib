# -*- coding: utf-8 -*-
"""
    nlglib.ctx
    ~~~~~~~~~~

    Implements the objects required to keep the context.

    :copyright: (c) 2015 by Armin Ronacher, (c) 2017 by Roman Kutlak
    :license: BSD, see LICENSE for more details.
"""

import sys
from functools import update_wrapper

from ._compat import BROKEN_PYPY_CTXMGR_EXIT, reraise
from .globals import _pipeline_ctx_stack
from .signals import pipeline_context_pushed, pipeline_context_popped


# a singleton sentinel value for parameter defaults
_sentinel = object()


def has_pipeline_context():
    """Works like :func:`has_request_context` but for the pipeline
    context.  You can also just do a boolean check on the
    :data:`current_pipeline` object instead.

    .. versionadded:: 0.9
    """
    return _pipeline_ctx_stack.top is not None


def copy_current_pipeline_context(f):
    """A helper function that decorates a function to retain the current
    pipeline context. This is useful when working with greenlets. The moment
    the function is decorated a copy of the pipeline context is created and
    then pushed when the function is called.

    Example::

        import gevent
        from nlglib import copy_current_pipeline_context

        def process():
            @copy_current_request_context
            def do_some_work():
                # do some work here, it can access flask.request like you
                # would otherwise in the view function.
                ...
            gevent.spawn(do_some_work)
            return 'Regular response'

    """
    top = _pipeline_ctx_stack.top
    if top is None:
        raise RuntimeError('This decorator can only be used at local scopes '
                           'when a pipeline context is on the stack.')
    pipectx = top.copy()

    def wrapper(*args, **kwargs):
        with pipectx:
            return f(*args, **kwargs)
    return update_wrapper(wrapper, f)


class PipelineContext(object):
    """The pipeline context binds an pipeline object implicitly
    to the current thread or greenlet, similar to how the
    :class:`RequestContext` binds request information.  The pipeline
    context is also implicitly created if a request context is created
    but the pipeline is not on top of the individual pipeline
    context.
    """

    def __init__(self, pipeline, config):
        self.pipeline = pipeline
        self.lexicon = pipeline.lexicon
        conf = dict(self.pipeline.config)
        conf.update(config)
        self.config = pipeline.make_config(mappings=conf)

        # Like request context, pipeline contexts can be pushed multiple times
        # but there a basic "refcount" is enough to track them.
        self._refcnt = 0

    @property
    def stages(self):
        return self.config

    def push(self):
        """Binds the pipeline context to the current context."""
        self._refcnt += 1
        if hasattr(sys, 'exc_clear'):
            sys.exc_clear()
        _pipeline_ctx_stack.push(self)
        pipeline_context_pushed.send(self.pipeline)

    def pop(self, exc=_sentinel):
        """Pops the pipeline context."""
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.pipeline.do_teardown_pipeline_context(exc)
        finally:
            rv = _pipeline_ctx_stack.pop()
        assert rv is self, 'Popped wrong pipeline context.  (%r instead of %r)' \
            % (rv, self)
        pipeline_context_popped.send(self.pipeline)

    def copy(self):
        """Creates a copy of this pipeline context with the same pipeline object.
        This can be used to move a pipeline context to a different greenlet.
        Because the actual pipeline object is the same this cannot be used to
        move a pipeline context to a different thread unless access to the
        pipeline object is locked.

        """
        return self.__class__(self.pipeline)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop(exc_value)

        if BROKEN_PYPY_CTXMGR_EXIT and exc_type is not None:
            reraise(exc_type, exc_value, tb)
