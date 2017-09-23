# -*- coding: utf-8 -*-
"""
    nlglib.ctx
    ~~~~~~~~~~

    Implements the objects required to keep the context.

    :copyright: (c) 2015 by Armin Ronacher, (c) 2017 by Roman Kutlak
    :license: BSD, see LICENSE for more details.
"""

import sys

from copy import deepcopy
from functools import update_wrapper

from ._compat import BROKEN_PYPY_CTXMGR_EXIT, reraise
from .globals import _pipeline_ctx_stack, _linguistic_ctx_stack, _lexicon_ctx_stack
from .signals import pipeline_context_pushed, pipeline_context_popped
from .signals import linguistic_context_pushed, linguistic_context_popped
from .signals import lexicon_context_pushed, lexicon_context_popped
from .structures import NounPhrase, Coordination, Element, is_noun_t


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
                # do some work here, it can access nlglib.pipeline_context like you
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
        conf = dict(self.pipeline.config)
        if config:
            conf.update(config)
        self.config = pipeline.make_config(mappings=conf)
        # globals
        self.g = {}

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
        assert rv is self, 'Popped wrong pipeline context. ' \
                           '(%r instead of %r)' % (rv, self)
        pipeline_context_popped.send(self.pipeline)

    def copy(self):
        """Creates a copy of this pipeline context with the same pipeline object.
        This can be used to move a pipeline context to a different greenlet.
        Because the actual pipeline object is the same this cannot be used to
        move a pipeline context to a different thread unless access to the
        pipeline object is locked.

        """
        return self.__class__(self.pipeline, self.config)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop(exc_value)

        if BROKEN_PYPY_CTXMGR_EXIT and exc_type is not None:
            reraise(exc_type, exc_value, tb)


class LexiconContext(object):
    """The lexicon context binds an lexicon object implicitly
    to the current thread or greenlet, similar to how the
    :class:`PipelineContext` binds request information.  The lexicon
    context is also implicitly created if a pipeline context is created
    but the lexicon is not on top of the individual lexicon
    context.
    """

    def __init__(self, lexicon):
        self.lexicon = lexicon
        # Like pipeline context, lexicon contexts can be pushed multiple times
        # but there a basic "refcount" is enough to track them.
        self._refcnt = 0

    def push(self):
        """Binds the lexicon context to the current context."""
        self._refcnt += 1
        if hasattr(sys, 'exc_clear'):
            sys.exc_clear()
        _lexicon_ctx_stack.push(self)
        lexicon_context_pushed.send(self.lexicon)

    def pop(self, exc=_sentinel):
        """Pops the lexicon context."""
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.lexicon.do_teardown_lexicon_context(exc)
        finally:
            rv = _lexicon_ctx_stack.pop()
        assert rv is self, 'Popped wrong lexicon context. ' \
                           '(%r instead of %r)' % (rv, self)
        lexicon_context_popped.send(self.lexicon)

    def copy(self):
        """Creates a copy of this lexicon context with the same lexicon object.
        This can be used to move a lexicon context to a different greenlet.
        Because the actual lexicon object is the same this cannot be used to
        move a lexicon context to a different thread unless access to the
        lexicon object is locked.

        """
        return self.__class__(self.lexicon)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop(exc_value)

        if BROKEN_PYPY_CTXMGR_EXIT and exc_type is not None:
            reraise(exc_type, exc_value, tb)


class LinguisticContext(object):
    def __init__(self, ontology=None, pipeline=None):
        self.pipeline = pipeline
        self.ontology = ontology
        self.referents = dict()
        self.referent_stack = []
        self.np_stack = []
        self.history = []
        # this can be used for direct speech or system/user customisation
        self.speakers = []
        self.hearers = []

    def is_speaker(self, element):
        """Return True if the element is a speaker. """
        return element in self.speakers

    def is_last_speaker(self, element):
        """Return True if the element is the current (last) speaker. """
        return element in self.speakers[-1:]

    def add_speaker(self, element):
        """Add the `element` to the list of speakers as the last speaker. """
        self.speakers.append(element)

    def remove_speaker(self, element):
        """Delete the `element` from the list of speakers. """
        self.speakers.remove(element)

    def remove_last_speaker(self):
        """If there are any speakers, remove the last one and return it. """
        if self.speakers:
            return self.speakers.pop()

    def is_hearer(self, element):
        """Return True if the given elemen is a hearer. """
        return element in self.hearers

    def is_last_hearer(self, element):
        """Return True if the given elemen is the current (last) hearer. """
        return element in self.hearers[:-1]

    def add_hearer(self, element):
        """Add the `element` to the list of hearers as the last hearer. """
        self.hearers.append(element)

    def remove_hearer(self, element):
        """Delete the `element` from the list of hearers. """
        self.hearers.remove(element)

    def remove_last_hearer(self):
        """If there are any hearers, remove the last one and return it. """
        if self.hearers:
            return self.hearers.pop()

    def add_sentence(self, sent):
        """Add a sentence to the context. """
        self.history.append(sent)
        # add potential referents/distractors
        self._update_referents(sent)

    def _update_referents(self, sent):
        """Extract NPs and add them on the referent stack. Add subject last. """
        nps = [x for x in sent.constituents()
               if isinstance(x, NounPhrase) or
               (isinstance(x, Coordination) and
                isinstance(x.coords[0], NounPhrase))]
        for np in nps:
            nouns = [x for x in np.constituents() if is_noun_t(x)]
            self.referent_stack.extend(reversed(nouns))
            unspec_np = deepcopy(np)
            unspec_np.spec = Element()
            self.np_stack.append(unspec_np)

    def push(self):
        """Binds the pipeline context to the current context."""
        _linguistic_ctx_stack.push(self)
        linguistic_context_pushed.send(self)

    def pop(self):
        """Pops the pipeline context."""
        rv = _linguistic_ctx_stack.pop()
        assert rv is self, 'Popped wrong pipeline context. ' \
                           '(%r instead of %r)' % (rv, self)
        linguistic_context_popped.send(self)

    def copy(self):
        """Creates a copy of this pipeline context with the same pipeline object.
        This can be used to move a pipeline context to a different greenlet.
        Because the actual pipeline object is the same this cannot be used to
        move a pipeline context to a different thread unless access to the
        pipeline object is locked.

        """
        rv = self.__class__(self.ontology, self.pipeline)
        rv.referents = self.referents.copy()
        rv.referent_stack = self.referent_stack[:]
        rv.np_stack = self.np_stack[:]
        rv.history = self.history[:]
        rv.speakers = self.speakers[:]
        rv.hearers = self.hearers[:]

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop()

        if BROKEN_PYPY_CTXMGR_EXIT and exc_type is not None:
            reraise(exc_type, exc_value, tb)
