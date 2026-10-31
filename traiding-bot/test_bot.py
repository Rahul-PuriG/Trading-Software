import argparse
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bot


class PaperTradingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        default = patch("bot.DEFAULT_LOG", Path(self.temp.name) / "activity.jsonl")
        default.start()
        self.addCleanup(default.stop)

    def test_log_appends_without_overwriting_and_correlates_run(self):
        path = Path(self.temp.name) / "nested" / "activity.jsonl"
        first = bot.ActivityLog(path)
        first.write("submit_requested", symbol="AAPL")
        first.write("order_status", status="Submitted")
        second = bot.ActivityLog(path)
        second.write("cancel_requested")
        records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["run_id"], records[1]["run_id"])
        self.assertNotEqual(records[1]["run_id"], records[2]["run_id"])
        self.assertTrue(records[0]["time"].endswith("+00:00"))

    @patch("bot.IB")
    def test_fill_snapshot_is_recorded_and_filtered(self, ib_class):
        ib = ib_class.return_value
        ib.managedAccounts.return_value = ["DU123"]
        def fill(account):
            return SimpleNamespace(contract=SimpleNamespace(symbol="AAPL"),
                execution=SimpleNamespace(execId="exec1", acctNumber=account,
                    orderId=42, permId=99, clientId=17, side="BOT", shares=1,
                    price=100, time="2026-10-31T12:00:00+00:00"))
        ib.reqExecutions.return_value = [fill("DU123"), fill("DU999")]
        self.assertEqual(bot.run(bot.parser().parse_args(["fills"])), 0)
        records = [json.loads(line) for line in bot.DEFAULT_LOG.read_text().splitlines()]
        snapshot = next(r for r in records if r["event"] == "execution_snapshot")
        self.assertEqual(len(snapshot["fills"]), 1)
        self.assertEqual(snapshot["fills"][0]["execution_id"], "exec1")
        ib.placeOrder.assert_not_called()

    def test_live_or_mixed_sessions_are_rejected(self):
        for accounts in ([], ["U123"], ["DU123", "U123"]):
            with self.subTest(accounts=accounts), self.assertRaises(ValueError):
                bot.paper_account(accounts)

    def test_account_selection(self):
        self.assertEqual(bot.paper_account(["DU123"]), "DU123")
        self.assertEqual(bot.paper_account(["DU123", "DU456"], "DU456"), "DU456")
        for requested in (None, "DU999"):
            with self.assertRaises(ValueError):
                bot.paper_account(["DU123", "DU456"], requested)

    def test_invalid_order_numbers_are_rejected(self):
        for value in ("0", "-1", "NaN", "Infinity", "abc", "1e999"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                bot.positive_number(value)

    @patch("bot.IB")
    def test_preview_does_not_submit(self, ib_class):
        ib = ib_class.return_value
        ib.managedAccounts.return_value = ["DU123"]
        ib.qualifyContracts.return_value = [SimpleNamespace(conId=123, symbol="AAPL")]
        args = bot.parser().parse_args(["order", "AAPL", "BUY", "1", "100"])
        self.assertEqual(bot.run(args), 0)
        ib.placeOrder.assert_not_called()
        ib.disconnect.assert_called_once()

    @patch("bot.IB")
    def test_live_session_never_submits(self, ib_class):
        ib = ib_class.return_value
        ib.managedAccounts.return_value = ["U123"]
        args = bot.parser().parse_args(["order", "AAPL", "BUY", "1", "100", "--submit"])
        with self.assertRaises(ValueError):
            bot.run(args)
        ib.placeOrder.assert_not_called()
        ib.disconnect.assert_called_once()

    @patch("bot.IB")
    def test_cancel_rejects_other_client_order(self, ib_class):
        ib = ib_class.return_value
        ib.managedAccounts.return_value = ["DU123"]
        ib.reqOpenOrders.return_value = [SimpleNamespace(
            order=SimpleNamespace(orderId=42, clientId=99, account="DU123"))]
        args = bot.parser().parse_args(["cancel", "42", "--submit"])
        with self.assertRaises(ValueError):
            bot.run(args)
        ib.cancelOrder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
