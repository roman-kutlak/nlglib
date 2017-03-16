import logging
import os
import sys

from threading import Lock
from werkzeug.datastructures import ImmutableDict

from nlglib.nlg import Nlg
from nlglib.macroplanning import formula_to_rst
from nlglib.fol import expr
from nlglib.simplifications import simplification_ops
from nlglib.simplifications import Heuristic
from nlglib.reg import Context
from .utils import _PackageBoundObject, locked_cached_property, find_package
from .config import Config, ConfigAttribute

_logger_lock = Lock()


def translate(formula, templates=None, simplifications=None):
    if isinstance(formula, str):
        formulas = [expr(f) for f in formula.split(';') if f.strip()]
    pipeline = Nlg()
    context = Context(ontology=None)
    context.templates = templates or {}
    doc = []
    for f in formulas:
        if simplifications:
            for s in filter(lambda x: x in simplification_ops, simplifications):
                f = simplification_ops[s](f)
        doc.append(formula_to_rst(f))

    translations = pipeline.process_nlg_doc2(doc, None, context)
    return translations

# def minimise_search(f, h_file, ops=LOGIC_OPS, max=-1):


class Pipeline(_PackageBoundObject):

    debug = ConfigAttribute('DEBUG')
    logger_name = ConfigAttribute('LOGGER_NAME')

    # noinspection PyTypeChecker
    #: Default configuration parameters.
    default_config = ImmutableDict({
        'DEBUG': False,
        'LOGGER_NAME': None,
    })

    def __init__(self, import_name, instance_path=None,
                 instance_relative_config=False, root_path=None):
        _PackageBoundObject.__init__(self, import_name, root_path=root_path)
        #: Holds the path to the instance folder.
        if instance_path is None:
            instance_path = self.auto_find_instance_path()
        elif not os.path.isabs(instance_path):
            raise ValueError('If an instance path is provided it must be '
                             'absolute.  A relative path was given instead.')
        self.instance_path = instance_path

        #: The configuration dictionary as :class:`Config`.  This behaves
        #: exactly like a regular dictionary but supports additional methods
        #: to load a config from files.
        self.config = self.make_config(instance_relative_config)

        # Prepare the deferred setup of the logger.
        self._logger = None
        self.logger_name = self.import_name

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
