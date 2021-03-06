#
# Copyright 2015, Couchbase, Inc.
# All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function
import json

from couchbase.tests.base import CouchbaseTestCase
from couchbase.n1ql import N1QLQuery, CONSISTENCY_REQUEST, CONSISTENCY_NONE


class N1QLStringTest(CouchbaseTestCase):
    def setUp(self):
        super(N1QLStringTest, self).setUp()

    def test_encode_namedargs(self):
        qstr = 'SELECT * FROM default WHERE field1=$arg1 AND field2=$arg2'
        q = N1QLQuery(qstr, arg1='foo', arg2='bar')

        self.assertEqual(qstr, q.statement)

        dval = json.loads(q.encoded)
        self.assertEqual(qstr, dval['statement'])
        self.assertEqual('foo', dval['$arg1'])
        self.assertEqual('bar', dval['$arg2'])

    def test_encode_posargs(self):
        qstr = 'SELECT * FROM default WHERE field1=$1 AND field2=$arg2'
        q = N1QLQuery(qstr, 'foo', 'bar')
        dval = json.loads(q.encoded)
        self.assertEqual(qstr, dval['statement'])
        self.assertEqual('foo', dval['args'][0])
        self.assertEqual('bar', dval['args'][1])

    def test_encode_mixed_args(self):
        qstr = 'SELECT * FROM default WHERE field1=$1 AND field2=$arg2'
        q = N1QLQuery(qstr, 'foo', arg2='bar')
        dval = json.loads(q.encoded)
        self.assertEqual('bar', dval['$arg2'])
        self.assertEqual('foo', dval['args'][0])
        self.assertEqual(1, len(dval['args']))

    def test_encoded_consistency(self):
        qstr = 'SELECT * FROM default'
        q = N1QLQuery(qstr)
        q.consistency = CONSISTENCY_REQUEST
        dval = json.loads(q.encoded)
        self.assertEqual('request_plus', dval['scan_consistency'])

        q.consistency = CONSISTENCY_NONE
        dval = json.loads(q.encoded)
        self.assertEqual('none', dval['scan_consistency'])

    def test_encode_scanvec(self):
        # The value is a vbucket's sequence number,
        # and guard is a vbucket's UUID.

        q = N1QLQuery('SELECT * FROM default')

        q._add_scanvec((42, 3004, 3))
        dval = json.loads(q.encoded)
        sv_exp = {
            '42': {'value': 3, 'guard': '3004'}
        }

        self.assertEqual('at_plus', dval['scan_consistency'])
        self.assertEqual(sv_exp, dval['scan_vector'])

        # Ensure the vb field gets updated. No duplicates!
        q._add_scanvec((42, 3004, 4))
        sv_exp['42']['value'] = 4
        dval = json.loads(q.encoded)
        self.assertEqual(sv_exp, dval['scan_vector'])

        q._add_scanvec((91, 7779, 23))
        dval = json.loads(q.encoded)
        sv_exp['91'] = {'guard': '7779', 'value': 23}
        self.assertEqual(sv_exp, dval['scan_vector'])
