"""Проверка границ правил и порогов без создания нагрузки."""
import copy
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import psutil
import inventory
import monitor


class LabTests(unittest.TestCase):
    def passport(self, ram=8, cores=4, disk=85, available=2):
        return {'memory': {'total_gb': ram, 'available_gb': available},
                'cpu': {'physical_cores': cores},
                'disks': [{'device': 'C:', 'used_percent': disk}]}

    def test_rules_and_boundaries(self):
        self.assertEqual(inventory.analyze(self.passport()), [])
        self.assertEqual(len(inventory.analyze(self.passport(7.9, 3, 85.1, 1.9))), 4)
        self.assertEqual(len(inventory.analyze(self.passport(16, 6))), 1)
        self.assertEqual(inventory.analyze(self.passport(16, None)), [])

    def test_threshold_inclusive(self):
        self.assertEqual(len(monitor.check_alerts({'cpu': 70, 'ram': 90, 'disk': 85})), 3)
        self.assertEqual(monitor.check_alerts({'cpu': 69.9, 'ram': 89.9, 'disk': 84.9}), [])

    def test_network_multiple_ipv4_and_no_ipv4(self):
        def addr(family, address, mask=None):
            return SimpleNamespace(family=family, address=address, netmask=mask)
        data = {'a': [addr(socket.AF_INET, '10.0.0.1', '255.0.0.0'),
                      addr(psutil.AF_LINK, 'AA-BB'),
                      addr(socket.AF_INET, '10.0.0.2', '255.0.0.0')],
                'b': [addr(psutil.AF_LINK, 'CC-DD')]}
        with patch('inventory.psutil.net_if_addrs', return_value=data):
            result = inventory.get_network_info()
        self.assertEqual(len(result), 2)
        self.assertTrue(all(item['mac'] == 'AA-BB' for item in result))

    def test_summary(self):
        rows = [{key: value for key in ('cpu', 'ram', 'disk', 'uptime_hours')}
                for value in (10, 20, 30)]
        self.assertEqual(monitor.summarize(rows)['cpu'], {'mean': 20, 'min': 10, 'max': 30})


if __name__ == '__main__':
    unittest.main(verbosity=2)
