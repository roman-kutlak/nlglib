import os

# remove multiple spaces
def trim(str):
    return ' '.join(str.strip().split())


class Settings:
    """ Class Settings reads a file with various settings such as paths to
        domain definition files, paths to file with plans, etc.

        """

    def __init__(self, filename):
        # assume the file contains key value pairs with no spaces
        self.table = dict()
        try:
            with open(filename) as f:
                for line in f:
                    kv = line.split()
                    if len(kv) > 1:
                        self.table[kv[0]] = kv[1]

        except IOError:
            # This should probably log the exception...
            print("Something wrong with the file '%s'" % filename)

    def get_setting(self, key):
        if key in self.table:
            return self.table[key]
        else:
            return None

"""
    Look for a default settings file in $HOME/.sassy/sassy.prefs
    and create a Settings object using that file.

    """
def get_user_settings():
    home = os.getenv("HOME")
    path = os.sep.join([home, ".sassy/sassy.prefs"])
    return Settings(path)

