import unittest

from fx_account import Costs, FXAccount, Quote, pnl_usd


class FXAccountTests(unittest.TestCase):
    def test_currency_conversion_for_long_and_short(self):
        self.assertAlmostEqual(pnl_usd("BUY",10000,150,151),10000/151)
        self.assertAlmostEqual(pnl_usd("SELL",10000,150,149),10000/149)

    def test_risk_budget_includes_both_commissions_and_stop_slippage(self):
        account=FXAccount()
        plan=account.plan("SELL",156.322,156.405,Quote(156.35,156.36))
        self.assertEqual(plan.risk_budget,100)
        self.assertLessEqual(plan.planned_stop_risk,100+1e-8)
        # One further unit must breach either risk or available-margin capacity.
        more=plan.units+1
        risk=-pnl_usd("SELL",more,plan.expected_entry,plan.expected_stop_fill)+2*account.costs.commission(more)
        self.assertGreater(risk,100)

    def test_overlapping_trade_uses_remaining_available_funds(self):
        account=FXAccount()
        quote=Quote(150,150.01)
        first=account.plan("BUY",150.01,149,quote)
        account.open("first",first,first.expected_entry,quote)
        free=account.available(quote)
        second=account.plan("BUY",150.01,149,quote)
        self.assertAlmostEqual(second.risk_budget,free*.01)
        self.assertLess(second.risk_budget,100)
        account.open("second",second,second.expected_entry,quote)
        self.assertEqual(len(account.positions),2)
        self.assertAlmostEqual(account.margin,(first.units+second.units)/50)
        self.assertGreaterEqual(account.available(quote),-1e-8)

    def test_cash_margin_constraint_prevents_overleveraging_with_tight_stop(self):
        account=FXAccount(costs=Costs(spread_pips=0,slippage_pips=0,commission_min=0,commission_rate=0))
        quote=Quote(150,150)
        plan=account.plan("BUY",150,149.9999,quote)
        self.assertEqual(plan.units,500000)
        account.open("full",plan,150,quote)
        self.assertEqual(account.available(quote),0)
        self.assertEqual(account.plan("BUY",150,149.9999,quote).units,0)

    def test_closing_releases_margin_and_charges_each_fee_once(self):
        account=FXAccount();quote=Quote(150,150.01)
        plan=account.plan("BUY",150.01,149,quote)
        position=account.open("trade",plan,plan.expected_entry,quote)
        result=account.close("trade",position.target,"target")
        self.assertAlmostEqual(account.balance,10000+result['net_pnl_usd'])
        self.assertEqual(account.margin,0)
        self.assertAlmostEqual(result['commission_usd'],2*account.costs.commission(plan.units))

    def test_open_profit_changes_available_funds_not_realized_balance(self):
        account=FXAccount();quote=Quote(150,150.01)
        plan=account.plan("BUY",150.01,149,quote)
        account.open("trade",plan,plan.expected_entry,quote)
        balance=account.balance
        self.assertGreater(account.available(Quote(151,151.01)),account.available(quote))
        self.assertEqual(account.balance,balance)

    def test_same_trade_id_cannot_be_submitted_twice(self):
        account=FXAccount();quote=Quote(150,150.01)
        plan=account.plan("BUY",150.01,149,quote)
        account.open("trade",plan,plan.expected_entry,quote)
        with self.assertRaises(ValueError):account.open("trade",plan,plan.expected_entry,quote)

    def test_gap_at_fill_can_exceed_budget_and_size_is_not_silently_changed(self):
        account=FXAccount();quote=Quote(150,150.01)
        plan=account.plan("BUY",150.01,149,quote)
        position=account.open("gap",plan,151,Quote(151,151.01))
        self.assertEqual(position.units,plan.units)
        self.assertGreater(position.risk_at_fill,position.risk_budget)

    def test_old_plans_do_not_bypass_changed_margin_capacity(self):
        account=FXAccount(costs=Costs(spread_pips=0,slippage_pips=0,commission_min=0,commission_rate=0))
        quote=Quote(150,150)
        plan=account.plan("BUY",150,149.9999,quote)
        account.open("first",plan,150,quote)
        with self.assertRaises(ValueError):account.open("second",plan,150,quote)


if __name__ == "__main__":
    unittest.main()
