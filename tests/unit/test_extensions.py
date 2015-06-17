# Copyright 2015 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the
#    License. You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing,
#    software distributed under the License is distributed on an "AS
#    IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#    express or implied. See the License for the specific language
#    governing permissions and limitations under the License.

import unittest

import mock

from timid import entry
from timid import extensions


class ExtensionForTest(extensions.Extension):
    priority = 10


class ExtensionTest(unittest.TestCase):
    @mock.patch.object(entry, 'points', {
        extensions.NAMESPACE_EXTENSIONS: [
            mock.Mock(priority=5, ext='ext1'),
            mock.Mock(priority=0, ext='ext0'),
            mock.Mock(priority=10, ext='ext2'),
            mock.Mock(priority=10, ext='ext3'),
        ],
    })
    def test_extensions(self):
        result = extensions.Extension.extensions()

        self.assertEqual([r.ext for r in result],
                         ['ext0', 'ext1', 'ext2', 'ext3'])

    def test_activate(self):
        result = ExtensionForTest.activate('ctxt', 'args')

        self.assertEqual(result, None)

    def test_pre_step(self):
        obj = ExtensionForTest()

        result = obj.pre_step('ctxt', 'step', 5)

        self.assertEqual(result, None)

    def test_finalize(self):
        obj = ExtensionForTest()

        result = obj.finalize('ctxt', 'retval')

        self.assertEqual(result, 'retval')
