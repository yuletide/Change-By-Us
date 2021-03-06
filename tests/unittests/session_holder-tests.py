"""
    :copyright: (c) 2011 Local Projects, all rights reserved
    :license: Affero GNU GPL v3, see LICENSE for more details.
"""

"""
Session holder module.

"""
from unittest2 import TestCase
from framework.session_holder import SessionHolder


class ConfigTest (TestCase):
    """
    Container for session holder tests.

    """

    def test_set(self):
        """
        Test `set` methods.

        """
        data = {'testing': True}
        return_data = SessionHolder.set(data)

        self.assertEqual(return_data, data)
        self.assertIsInstance(return_data, dict)

    def test_get(self):
        """
        Test `get_session` methods.

        """
        data = {'testing': True}
        SessionHolder.session = data
        return_data = SessionHolder.get_session()

        self.assertEqual(return_data, data)
        self.assertIsInstance(return_data, dict)
