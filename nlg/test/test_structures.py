import unittest

import nlg.structures as dstruct


class TestMessage(dstruct.MessageSpec):
    """ A dummy message specification for testing. """

    def foo(self):
        """ A simple method that is acting as a kye and returns value 'bar' """
        return 'bar'


class TestMessageSpec(unittest.TestCase):

    def test_value_for(self):
        tm = TestMessage('some_name')
        self.assertEqual('bar', tm.value_for('foo'))

        self.assertRaises(ValueError, tm.value_for, 'baz')


if __name__ == '__main__':
    unittest.main()
