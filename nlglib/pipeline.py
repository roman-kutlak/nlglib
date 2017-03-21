import logging
import os
import sys

from contextlib import ContextDecorator
from threading import Lock
from werkzeug.datastructures import ImmutableDict

from . import macroplanning, lexicalisation, aggregation, reg, realisation, format

from .config import Config, ConfigAttribute
from .utils import PackageBoundObject, locked_cached_property, find_package

_logger_lock = Lock()


class Pipeline(PackageBoundObject):
    debug = ConfigAttribute('DEBUG')
    logger_name = ConfigAttribute('LOGGER_NAME')

    # noinspection PyTypeChecker
    #: Default configuration parameters.
    default_config = ImmutableDict({
        'DEBUG': False,
        'LOGGER_NAME': None,
        'CONTENT_PREPROCESSING': macroplanning.preprocess_content,
        'CONTENT_SELECTION': macroplanning.select_content,
        'CONTENT_AGGREGATION': macroplanning.aggregate_content,
        'CONTENT_STRUCTURING': macroplanning.structure_content,
        'LEXICALISATION': lexicalisation.lexicalise,
        'AGGREGATION': aggregation.aggregate,
        'PRONOMINALISATION': None,
        'REFERRING': reg.generate_re,
        'REALISATION': realisation.realise,
        'FORMATTING': format.to_text
    })

    _logger = None
    context = None

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

    def process(self, data, **kwargs):
        kwargs['_pipeline'] = self
        if not self.context:
            self.context = PipelineContext(self)
        kwargs_ = self.context.kwargs.copy()
        kwargs_.update(kwargs)
        rv = data
        # TODO: add pre/post signals
        for name in self.stages:
            self.logger.debug('running stage {}.'.format(name))
            func = self.context.stages.get(name)
            if func:
                rv = func(rv, **kwargs_)
            else:
                self.logger.debug('    --> skipping stage {}.'.format(name))
            self.logger.debug('finished stage {}.'.format(name))
        return rv

    def make_config(self, instance_relative=False):
        """Used to create the config attribute by the Flask constructor.
        The `instance_relative` parameter is passed in from the constructor
        of Flask (there named `instance_relative_config`) and indicates if
        the config should be relative to the instance path or the root path
        of the application.

        """
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


class PipelineContext(ContextDecorator):
    def __init__(self, pipeline=None, **kwargs):
        self.pipeline = pipeline
        self.kwargs = dict(kwargs)
        self.stages = dict([
            ('CONTENT_PREPROCESSING', self.pipeline.config.get('CONTENT_PREPROCESSING')),
            ('CONTENT_SELECTION', self.pipeline.config.get('CONTENT_SELECTION')),
            ('CONTENT_AGGREGATION', self.pipeline.config.get('CONTENT_AGGREGATION')),
            ('CONTENT_STRUCTURING', self.pipeline.config.get('CONTENT_STRUCTURING')),
            ('LEXICALISATION', self.pipeline.config.get('LEXICALISATION')),
            ('AGGREGATION', self.pipeline.config.get('AGGREGATION')),
            ('PRONOMINALISATION', self.pipeline.config.get('PRONOMINALISATION')),
            ('REFERRING', self.pipeline.config.get('REFERRING')),
            ('REALISATION', self.pipeline.config.get('REALISATION')),
            ('FORMATTING', self.pipeline.config.get('FORMATTING')),
        ])

    def __enter__(self):
        self.original_context = self.pipeline.context
        self.pipeline.context = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pipeline.context = self.original_context
        self.original_context = None
        del self.__dict__['pipeline']
        return False
