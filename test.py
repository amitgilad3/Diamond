#!/usr/bin/python
################################################################################

import os
import sys
import unittest
import inspect
import traceback

from StringIO import StringIO
from contextlib import nested

from mock import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'collectors')))

from diamond import *

def get_collector_config(key, value):
    config = configobj.ConfigObj()
    config['server'] = {}
    config['server']['collectors_config_path'] = ''
    config['collectors'] = {}
    config['collectors']['default'] = {}
    config['collectors'][key] = value
    return config

class CollectorTestCase(unittest.TestCase):
    def getFixturePath(self, fixture_name):
        file = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), 'fixtures', fixture_name)
        if not os.access(file, os.R_OK):
            print "Missing Fixture "+file
        return file

    def getFixture(self, fixture_name):
        file = open(self.getFixturePath(fixture_name), 'r')
        data = StringIO(file.read())
        file.close()
        return data

    def assertPublished(self, mock, key, value):
        calls = filter(lambda x: x[0][0] == key, mock.call_args_list)

        actual_value = len(calls)
        expected_value = 1
        message = '%s: actual number of calls %d, expected %d' % (key, actual_value, expected_value)

        self.assertEqual(actual_value, expected_value, message)

        actual_value = calls[0][0][1]
        expected_value = value
        precision = 0

        if isinstance(value, tuple):
            expected_value, precision = expected_value

        message = '%s: actual %r, expected %r' % (key, actual_value, expected_value)
        #print message

        if precision is not None:
            self.assertAlmostEqual(float(actual_value), float(expected_value), places = precision, msg = message)
        else:
            self.assertEqual(actual_value, expected_value, message)

    def assertPublishedMany(self, mock, dict):
        for key, value in dict.iteritems():
            self.assertPublished(mock, key, value)

        mock.reset_mock()

collectorTests = {}
def getCollectorTests(path):
    for f in os.listdir(path):
        cPath = os.path.abspath(os.path.join(path, f))
        if os.path.isfile(cPath) and len(f) > 3 and f[-3:] == '.py' and 'tests' in cPath:
            sys.path.append(os.path.join(os.path.dirname(cPath), '..'))
            sys.path.append(os.path.dirname(cPath))
            modname = inspect.getmodulename(cPath)
            try:
                # Import the module
                collectorTests[modname] = __import__(modname, globals(), locals(), ['*'])
                #print "Imported module: %s" % (modname)
            except Exception, e:
                print "Failed to import module: %s. %s" % (modname, traceback.format_exc())
                continue

    for f in os.listdir(path):
        cPath = os.path.abspath(os.path.join(path, f))
        if os.path.isdir(cPath):
            getCollectorTests(cPath)

cPath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'collectors'))
getCollectorTests(cPath)

################################################################################

if __name__ == "__main__":
    tests = []
    for module in collectorTests:
        test = None
        clsmembers = inspect.getmembers(sys.modules[module], inspect.isclass)
        for cls in clsmembers:
            for base in cls[1].__bases__:
                if issubclass(base, unittest.TestCase):
                    test = cls[0]
                    break
                if test:
                    break
        if not test:
            continue
        c = getattr(collectorTests[module], test)
        tests.append(unittest.TestLoader().loadTestsFromTestCase(c))
    suite = unittest.TestSuite(tests)
    unittest.TextTestRunner(verbosity=1).run(suite)