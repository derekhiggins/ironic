# Copyright 2017 Lenovo, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

STATE_POWER_ON = "power on"
STATE_POWER_OFF = "power off"
STATE_POWERING_ON = "power on"
STATE_POWERING_OFF = "power on"

import sys

import six

import mock

from oslo_utils import importutils

from ironic.common import states
from ironic.conductor import task_manager
from ironic.drivers.modules.xclarity import common
from ironic.drivers.modules.xclarity import power
from ironic.tests.unit.conductor import mgr_utils
from ironic.tests.unit.db import base as db_base
from ironic.tests.unit.db import utils as db_utils
from ironic.tests.unit.objects import utils as obj_utils

xclarity_constants = importutils.try_import('xclarity_client.constants')
xclarity_client_exceptions = importutils.try_import(
    'xclarity_client.exceptions')


@mock.patch.object(common, 'get_xclarity_client',
                   spect_set=True, autospec=True)
class XClarityPowerDriverTestCase(db_base.DbTestCase):

    def setUp(self):
        super(XClarityPowerDriverTestCase, self).setUp()
        self.config(enabled_hardware_types=['xclarity'],
                    enabled_power_interfaces=['xclarity'],
                    enabled_management_interfaces=['xclarity'])
        mgr_utils.mock_the_extension_manager(
            driver='xclarity', namespace='ironic.hardware.types')
        self.node = obj_utils.create_test_node(
            self.context,
            driver='xclarity',
            driver_info=db_utils.get_test_xclarity_driver_info())

    def test_get_properties(self, mock_get_xc_client):
        expected = common.REQUIRED_ON_DRIVER_INFO
        self.assertItemsEqual(expected,
                              self.node.driver_info)

    @mock.patch.object(common, 'get_server_hardware_id',
                       spect_set=True, autospec=True)
    def test_validate(self, mock_validate_driver_info, mock_get_xc_client):
        with task_manager.acquire(self.context, self.node.uuid) as task:
            task.driver.power.validate(task)
        common.get_server_hardware_id(task.node)
        mock_validate_driver_info.assert_called_with(task.node)

    @mock.patch.object(power.XClarityPower, 'get_power_state',
                       return_value=STATE_POWER_ON)
    def test_get_power_state(self, mock_get_power_state, mock_get_xc_client):
        with task_manager.acquire(self.context, self.node.uuid) as task:
            result = power.XClarityPower.get_power_state(task)
        self.assertEqual(STATE_POWER_ON, result)

    def test_get_power_state_fail(self, mock_xc_client):
        with task_manager.acquire(self.context, self.node.uuid) as task:
            xclarity_client_exceptions.XClarityError = Exception
            sys.modules['xclarity_client.exceptions'] = (
                xclarity_client_exceptions)
            if 'ironic.drivers.modules.xclarity' in sys.modules:
                six.moves.reload_module(
                    sys.modules['ironic.drivers.modules.xclarity'])
            ex = common.XClarityError('E')
            mock_xc_client.return_value.get_node_power_status.side_effect = ex
            self.assertRaises(common.XClarityError,
                              task.driver.power.get_power_state,
                              task)

    @mock.patch.object(power.XClarityPower, 'get_power_state',
                       return_value=states.POWER_ON)
    def test_set_power(self, mock_set_power_state, mock_get_xc_client):
        with task_manager.acquire(self.context, self.node.uuid) as task:
            task.driver.power.set_power_state(task, states.POWER_ON)
            expected = task.driver.power.get_power_state(task)
        self.assertEqual(expected, states.POWER_ON)

    def test_set_power_fail(self, mock_xc_client):
        with task_manager.acquire(self.context, self.node.uuid) as task:
            xclarity_client_exceptions.XClarityError = Exception
            sys.modules['xclarity_client.exceptions'] = (
                xclarity_client_exceptions)
            if 'ironic.drivers.modules.xclarity' in sys.modules:
                six.moves.reload_module(
                    sys.modules['ironic.drivers.modules.xclarity'])
            ex = common.XClarityError('E')
            mock_xc_client.return_value.set_node_power_status.side_effect = ex
            self.assertRaises(common.XClarityError,
                              task.driver.power.set_power_state,
                              task, states.POWER_OFF)
