import time
import unittest
from unittest.mock import patch

from ban_hammer import BanHammer, Action


class TestBanHammer(unittest.TestCase):
    def setUp(self):
        self.bans = {
            "login_failed": {
                "thresholds": [
                    {"limit": 3, "window": 600, "action": [Action.block_local], "action_duration": 86400},
                    {"limit": 2, "window": 600, "action": [Action.record_local], "action_duration": 86400}
                ]
            }
        }

    def test_incr_threshold_not_reached(self):
        token = "127.0.0.1"
        metric = "login_failed"
        banhammer = BanHammer(self.bans)
        passed = banhammer.incr(token, metric)
        self.assertTrue(passed)

    
    def test_incr_threshold_reached(self):
        token = "127.0.0.1"
        metric = "login_failed"
        banhammer = BanHammer(self.bans)
        banhammer.incr(token, metric)
        banhammer.incr(token, metric)
        passed = banhammer.incr(token, metric)
        self.assertFalse(passed)

    def test_incr_threshold_reached_with_stats(self):
        token = "127.0.0.1"
        metric = "login_failed"
        banhammer = BanHammer(self.bans, return_rates=True)
        now = time.time()
        within_10m  = now + 10*60 - 5
        within_60m  = now + 60*60 - 10
        with patch('time.time', return_value=now):
            banhammer.incr(token, metric)
        with patch('time.time', return_value=within_10m):
            banhammer.incr(token, metric)
        with patch('time.time', return_value=within_60m):
            passed = banhammer.incr(token, metric)

        self.assertEqual(passed, (True, {'token_rate_1m': 1, 'token_rate_10m': 1, 'token_rate_60m': 3}))

    def test_ban_config_sorting(self):
        pass

    def test_block(self):
        pass

    def test_unblock(self):
        pass

    def test_stats(self):
        pass
