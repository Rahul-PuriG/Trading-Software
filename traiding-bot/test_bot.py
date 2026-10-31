import argparse
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bot


class PaperTradingTests(unittest.TestCase):
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
