import sys
import os
import unittest

# we are assuming that the file runs from $(SASSY_ROOT)/tests
# and we need to import stuff from $(SASSY_ROOT)/src
# so append the dir to os.path
cwd = os.getcwd()
path = cwd.split(os.sep)
new_path = path[:-1]
new_path.append("src")
source = os.sep.join(new_path)
sys.path.insert(0, source)

if __name__ == '__main__':
    loader = unittest.TestLoader()
    tests = loader.discover('.', pattern="test_*.py")
    testRunner = unittest.runner.TextTestRunner(verbosity=2)
    testRunner.run(tests)
