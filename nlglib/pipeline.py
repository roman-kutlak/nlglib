import importlib
import inspect
import logging
import os
import sys

from contextlib import ContextDecorator
from threading import Lock
from werkzeug.datastructures import ImmutableDict

from . import macroplanning, lexicalisation, aggregation, reg, realisation, format

from .config import Config, ConfigAttribute
from .ctx import PipelineContext
from .globals import _pipeline_ctx_stack
from .signals import pipeline_context_tearing_down
from .utils import PackageBoundObject, locked_cached_property, find_package
from .lexicon import Lexicon

# a singleton sentinel value for parameter defaults
_sentinel = object()

_logger_lock = Lock()


def get_debug_flag(default=None):
    val = os.environ.get('NLGLIB_DEBUG')
    if not val:
        return default
    return val.lower() not in ('0', 'false', 'no')


class Pipeline(PackageBoundObject):
    #: The name of the logger to use.  By default the logger name is the
    #: package name passed to the constructor.
    #:
    #: .. versionadded:: 0.4
    logger_name = ConfigAttribute('LOGGER_NAME')

    #: The debug flag.  Set this to ``True`` to enable debugging of the
    #: application.  In debug mode the debugger will kick in when an unhandled
    #: exception occurs and the integrated server will automatically reload
    #: the application if changes in the code are detected.
    #:
    #: This attribute can also be configured from the config with the ``DEBUG``
    #: configuration key.  Defaults to ``False``.
    debug = ConfigAttribute('DEBUG')

    #: The testing flag.  Set this to ``True`` to enable the test mode of
    #: Flask extensions (and in the future probably also Flask itself).
    #: For example this might activate unittest helpers that have an
    #: additional runtime cost which should not be enabled by default.
    #:
    #: If this is enabled and PROPAGATE_EXCEPTIONS is not changed from the
    #: default it's implicitly enabled.
    #:
    #: This attribute can also be configured from the config with the
    #: ``TESTING`` configuration key.  Defaults to ``False``.
    testing = ConfigAttribute('TESTING')

    # noinspection PyTypeChecker
    #: Default configuration parameters.
    default_config = ImmutableDict({
        'DEBUG': get_debug_flag(default=False),
        'TESTING': False,
        'PROPAGATE_EXCEPTIONS': None,
        'PRESERVE_CONTEXT_ON_EXCEPTION': None,
        'LOGGER_NAME': None,
        'LEXICON': Lexicon,
        'CONTENT_PREPROCESSING': macroplanning.preprocess_content,
        'CONTENT_SELECTION': macroplanning.select_content,
        'CONTENT_AGGREGATION': macroplanning.aggregate_content,
        'CONTENT_STRUCTURING': macroplanning.structure_content,
        'LEXICALISATION': lexicalisation.lexicalise,
        'AGGREGATION': aggregation.aggregate,
        'PRONOMINALISATION': None,
        'REFERRING': reg.generate_re,
        'REALISATION': ('realisation.backends.simplenlg', 'realise'),
        'FORMATTING': format.to_text
    })

    _logger = None

    def __init__(self, import_name, instance_path=None,
                 instance_relative_config=False, root_path=None):
        PackageBoundObject.__init__(self, import_name, root_path=root_path)
        #: Holds the path to the instance folder.
        if instance_path is None:
            instance_path = self.auto_find_instance_path()
        elif not os.path.isabs(instance_path):
            raise ValueError('If an instance path is provided it must be '
                             'absolute.  A relative path was given instead.')
        self.instance_path = instance_path

        self.config = self.make_config(instance_relative_config)

        # Prepare the deferred setup of the logger.
        self.logger_name = self.import_name

        self.stages = [
            'CONTENT_PREPROCESSING',
            'CONTENT_SELECTION',
            'CONTENT_AGGREGATION',
            'CONTENT_STRUCTURING',
            'LEXICALISATION',
            'AGGREGATION',
            'PRONOMINALISATION',
            'REFERRING',
            'REALISATION',
            'FORMATTING',
        ]

        #: A list of functions that are called when the pipeline context
        #: is destroyed.
        self.teardown_pipeline_context_funcs = []
        self.lexicon = self.config['LEXICON']()

    def process(self, data, **kwargs):
        context = _pipeline_ctx_stack.top
        if not context:
            with self.pipeline_context(kwargs):
                return self.process(data, **kwargs)
        rv = data
        # TODO: add pre/post signals
        for name in self.stages:
            self.logger.debug('running stage {}.'.format(name))
            func = context.stages.get(name)
            if not func:
                self.logger.debug('    --> skipping stage {}.'.format(name))
                continue
            if isinstance(func, str):
                package, dot, obj = func.rpartition('.')
                if not dot:
                    raise RuntimeError('The function string has to contain the package.')
                func = (package, obj)
            if isinstance(func, tuple):
                pkg, obj = func
                package = importlib.import_module(pkg)
                obj = getattr(package, obj)
                if inspect.isclass(obj):
                    func = obj()
                else:
                    func = obj
            rv = func(rv, **kwargs)
            self.logger.debug('finished stage {}.'.format(name))
        return rv

    def make_config(self, instance_relative=False, mappings=None):
        """Used to create the config attribute by the Flask constructor.
        The `instance_relative` parameter is passed in from the constructor
        of Flask (there named `instance_relative_config`) and indicates if
        the config should be relative to the instance path or the root path
        of the application.

        """
        if mappings:
            return Config(self.root_path, mappings)
        root_path = self.root_path
        if instance_relative:
            root_path = self.instance_path
        return Config(root_path, self.default_config)

    @locked_cached_property
    def name(self):
        """The name of the application.  This is usually the import name
        with the difference that it's guessed from the run file if the
        import name is main.  This name is used as a display name when
        Flask needs the name of the application.  It can be set and overridden
        to change the value.

        """
        if self.import_name == '__main__':
            fn = getattr(sys.modules['__main__'], '__file__', None)
            if fn is None:
                return '__main__'
            return os.path.splitext(os.path.basename(fn))[0]
        return self.import_name

    @property
    def logger(self):
        """A :class:`logging.Logger` object for this application.  The
        default configuration is to log to stderr if the application is
        in debug mode.  This logger can be used to (surprise) log messages.
        Here some examples::
            app.logger.debug('A value for debugging')
            app.logger.warning('A warning occurred (%d apples)', 42)
            app.logger.error('An error occurred')

        """
        if self._logger and self._logger.name == self.logger_name:
            return self._logger
        with _logger_lock:
            if self._logger and self._logger.name == self.logger_name:
                return self._logger
            self._logger = rv = logging.getLogger(self.logger_name)
            return rv

    @property
    def propagate_exceptions(self):
        """Returns the value of the ``PROPAGATE_EXCEPTIONS`` configuration
        value in case it's set, otherwise a sensible default is returned.

        .. versionadded:: 0.7
        """
        rv = self.config['PROPAGATE_EXCEPTIONS']
        if rv is not None:
            return rv
        return self.testing or self.debug

    @property
    def preserve_context_on_exception(self):
        """Returns the value of the ``PRESERVE_CONTEXT_ON_EXCEPTION``
        configuration value in case it's set, otherwise a sensible default
        is returned.
        
        """
        rv = self.config['PRESERVE_CONTEXT_ON_EXCEPTION']
        if rv is not None:
            return rv
        return self.debug

    def auto_find_instance_path(self):
        """Tries to locate the instance path if it was not provided to the
        constructor of the application class.  It will basically calculate
        the path to a folder named ``instance`` next to your main file or
        the package.

        """
        prefix, package_path = find_package(self.import_name)
        if prefix is None:
            return os.path.join(package_path, 'instance')
        return os.path.join(prefix, 'var', self.name + '-instance')

    def do_teardown_pipeline_context(self, exc=_sentinel):
        """Called when a pipeline context is popped. """
        if exc is _sentinel:
            exc = sys.exc_info()[1]
        for func in reversed(self.teardown_pipeline_context_funcs):
            func(exc)
        pipeline_context_tearing_down.send(self, exc=exc)

    def pipeline_context(self, config=None):
        """Creates a :class:`~nlglib.ctx.PipelineContext` from the optional
        config and binds it to the current context. For as long as the pipeline is bound
        to the current context the :data:`nlglib.current_pipeline` points to that
        pipeline. This must be used in
        combination with the ``with`` statement because the pipeline is only bound
        to the current context for the duration of the ``with`` block.

        Example usage::

            with pipe.pipeline_context():
                do_something_with(pipe)

        The object returned can also be used without the ``with`` statement.
        The example above is doing exactly the same as this code::

            ctx = pipe.pipeline_context()
            ctx.push()
            try:
                do_something_with(pipeline)
            finally:
                ctx.pop()

        :param config: a config dict
        """
        return PipelineContext(self, config)


#
# class PipelineContext(ContextDecorator):
#     def __init__(self, pipeline=None, **kwargs):
#         self.pipeline = pipeline
#         self.kwargs = dict(kwargs)
#         self.stages = dict([
#             ('CONTENT_PREPROCESSING', self.pipeline.config.get('CONTENT_PREPROCESSING')),
#             ('CONTENT_SELECTION', self.pipeline.config.get('CONTENT_SELECTION')),
#             ('CONTENT_AGGREGATION', self.pipeline.config.get('CONTENT_AGGREGATION')),
#             ('CONTENT_STRUCTURING', self.pipeline.config.get('CONTENT_STRUCTURING')),
#             ('LEXICALISATION', self.pipeline.config.get('LEXICALISATION')),
#             ('AGGREGATION', self.pipeline.config.get('AGGREGATION')),
#             ('PRONOMINALISATION', self.pipeline.config.get('PRONOMINALISATION')),
#             ('REFERRING', self.pipeline.config.get('REFERRING')),
#             ('REALISATION', self.pipeline.config.get('REALISATION')),
#             ('FORMATTING', self.pipeline.config.get('FORMATTING')),
#         ])
#
#     def __enter__(self):
#         self.original_context = self.pipeline.context
#         self.pipeline.context = self
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.pipeline.context = self.original_context
#         self.original_context = None
#         del self.__dict__['pipeline']
#         return False
