import os
import sys
import pkgutil
import threading

from threading import RLock

# sentinel
_missing = object()


# remove multiple spaces
def trim(text):
    return ' '.join(text.strip().split())


def flatten(lst):
    """ Return a list where all elemts are items.
    Any encountered iterable will be expanded. Method is recursive.

    """
    result = []
    for x in lst:
        if isinstance(x, list):
            for y in flatten(x):
                result.append(y)
        else:
            if x is not None:
                result.append(x)
    return result


def total_seconds(td):
    """Returns the total seconds from a timedelta object.
    :param timedelta td: the timedelta to be converted in seconds
    :returns: number of seconds
    :rtype: int
    """
    return td.days * 60 * 60 * 24 + td.seconds


class LogPipe(threading.Thread):
    """ A pipe that runs in a separate thread and logs incoming messages.
    codereview.stackexchange.com/questions/6567/
    how-to-redirect-a-subprocesses-output-stdout-and-stderr-to-logging-module
    
    """

    def __init__(self, log_fn):
        """Setup the object with a logger and a loglevel
        and start the thread
        """
        threading.Thread.__init__(self)
        self.daemon = False
        self.log_fn = log_fn
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)

    def fileno(self):
        """Return the write file descriptor of the pipe
        """
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything.
        """
        for line in iter(self.pipeReader.readline, ''):
            self.log_fn(line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe.
        """
        os.close(self.fdWrite)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class locked_cached_property(object):
    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value.  Works like the one in Werkzeug but has a lock for
    thread safety.

    Based on a part of the flask package.
    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

    """

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func
        self.lock = RLock()

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        with self.lock:
            value = obj.__dict__.get(self.__name__, _missing)
            if value is _missing:
                value = self.func(obj)
                obj.__dict__[self.__name__] = value
            return value


class PackageBoundObject(object):
    """Base class for objects that need to know the root path and package name.

    Based on a part of the flask package.
    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

    """

    def __init__(self, import_name, root_path=None):
        #: The name of the package or module.  Do not change this once
        #: it was set by the constructor.
        self.import_name = import_name

        if root_path is None:
            root_path = get_root_path(self.import_name)

        #: Where is the app root located?
        self.root_path = root_path

    def open_resource(self, resource, mode='rb'):
        """Opens a resource from the application's resource folder.  To see
        how this works, consider the following folder structure::
            /myapplication.py
            /schema.sql
            /static
                /style.css
            /templates
                /layout.html
                /index.html
        If you want to open the :file:`schema.sql` file you would do the
        following::
            with app.open_resource('schema.sql') as f:
                contents = f.read()
                do_something_with(contents)
        :param resource: the name of the resource.  To access resources within
                         subfolders use forward slashes as separator.
        :param mode: resource file opening mode, default is 'rb'.
        """
        if mode not in ('r', 'rb'):
            raise ValueError('Resources can only be opened for reading')
        return open(os.path.join(self.root_path, resource), mode)


def get_root_path(import_name):
    """Returns the path to a package or cwd if that cannot be found.  This
    returns the path of a package or the folder that contains a module.
    Not to be confused with the package path returned by :func:`find_package`.

    Originally a part of the flask package.
    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

    """
    # Module already imported and has a file attribute.  Use that first.
    mod = sys.modules.get(import_name)
    if mod is not None and hasattr(mod, '__file__'):
        return os.path.dirname(os.path.abspath(mod.__file__))

    # Next attempt: check the loader.
    loader = pkgutil.get_loader(import_name)

    # Loader does not exist or we're referring to an unloaded main module
    # or a main module without path (interactive sessions), go with the
    # current working directory.
    if loader is None or import_name == '__main__':
        return os.getcwd()

    # For .egg, zipimporter does not have get_filename until Python 2.7.
    # Some other loaders might exhibit the same behavior.
    if hasattr(loader, 'get_filename'):
        filepath = loader.get_filename(import_name)
    else:
        # Fall back to imports.
        __import__(import_name)
        mod = sys.modules[import_name]
        filepath = getattr(mod, '__file__', None)

        # If we don't have a filepath it might be because we are a
        # namespace package.  In this case we pick the root path from the
        # first module that is contained in our package.
        if filepath is None:
            raise RuntimeError('No root path can be found for the provided '
                               'module "%s".  This can happen because the '
                               'module came from an import hook that does '
                               'not provide file name information or because '
                               'it\'s a namespace package.  In this case '
                               'the root path needs to be explicitly '
                               'provided.' % import_name)

    # filepath is import_name.py for a module, or __init__.py for a package.
    return os.path.dirname(os.path.abspath(filepath))


def find_package(import_name):
    """Finds a package and returns the prefix (or None if the package is
    not installed) as well as the folder that contains the package or
    module as a tuple.  The package path returned is the module that would
    have to be added to the pythonpath in order to make it possible to
    import the module.  The prefix is the path below which a UNIX like
    folder structure exists (lib, share etc.).

    Originally a part of the flask package.
    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

    """
    root_mod_name = import_name.split('.')[0]
    loader = pkgutil.get_loader(root_mod_name)
    if loader is None or import_name == '__main__':
        # import name is not found, or interactive/main module
        package_path = os.getcwd()
    else:
        # For .egg, zipimporter does not have get_filename until Python 2.7.
        if hasattr(loader, 'get_filename'):
            filename = loader.get_filename(root_mod_name)
        elif hasattr(loader, 'archive'):
            # zipimporter's loader.archive points to the .egg or .zip
            # archive filename is dropped in call to dirname below.
            filename = loader.archive
        else:
            # At least one loader is missing both get_filename and archive:
            # Google App Engine's HardenedModulesHook
            #
            # Fall back to imports.
            __import__(import_name)
            filename = sys.modules[import_name].__file__
        package_path = os.path.abspath(os.path.dirname(filename))

        # In case the root module is a package we need to chop of the
        # rightmost part.  This needs to go through a helper function
        # because of python 3.3 namespace packages.
        if _matching_loader_thinks_module_is_package(
                loader, root_mod_name):
            package_path = os.path.dirname(package_path)

    site_parent, site_folder = os.path.split(package_path)
    py_prefix = os.path.abspath(sys.prefix)
    if package_path.startswith(py_prefix):
        return py_prefix, package_path
    elif site_folder.lower() == 'site-packages':
        parent, folder = os.path.split(site_parent)
        # Windows like installations
        if folder.lower() == 'lib':
            base_dir = parent
        # UNIX like installations
        elif os.path.basename(parent).lower() == 'lib':
            base_dir = os.path.dirname(parent)
        else:
            base_dir = site_parent
        return base_dir, package_path
    return None, package_path


def _matching_loader_thinks_module_is_package(loader, mod_name):
    """Given the loader that loaded a module and the module this function
    attempts to figure out if the given module is actually a package.

    Originally a part of the flask package.
    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

    """
    # If the loader can tell us if something is a package, we can
    # directly ask the loader.
    if hasattr(loader, 'is_package'):
        return loader.is_package(mod_name)
    # importlib's namespace loaders do not have this functionality but
    # all the modules it loads are packages, so we can take advantage of
    # this information.
    elif (loader.__class__.__module__ == '_frozen_importlib' and
                  loader.__class__.__name__ == 'NamespaceLoader'):
        return True
    # Otherwise we need to fail with an error that explains what went
    # wrong.
    raise AttributeError(
        ('%s.is_package() method is missing but is required by Pipeline of '
         'PEP 302 import hooks.  If you do not use import hooks and '
         'you encounter this error please file a bug against Pipeline.') %
        loader.__class__.__name__)
