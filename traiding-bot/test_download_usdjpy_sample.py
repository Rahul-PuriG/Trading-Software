from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from download_usdjpy_sample import collect_series, serialize_bar, write_csv, coverage_report


class USDJPYDownloadTests(unittest.TestCase):
    def bar(self, stamp):
        return SimpleNamespace(date=stamp, open=150, high=151, low=149, close=150.5)

    def test_naive_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            serialize_bar(self.bar(datetime(2025, 1, 23, 10)))

    def test_output_sorted_deduplicated_clipped_and_cached(self):
        ib = Mock()
        early = self.bar(datetime(2025, 1, 23, 3, 59, tzinfo=timezone.utc))
        late = self.bar(datetime(2025, 1, 24, 4, tzinfo=timezone.utc))
        a = self.bar(datetime(2025, 1, 23, 4, tzinfo=timezone.utc))
        b = self.bar(datetime(2025, 1, 23, 4, 15, tzinfo=timezone.utc))
        ib.reqHistoricalData.return_value = [late, b, a, a, early]
        contract = SimpleNamespace(conId=123)
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            rows, info = collect_series(ib, contract, date(2025,1,23), date(2025,1,24), 15, folder)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["timestamp"], a.date.isoformat())
            cached, _ = collect_series(ib, contract, date(2025,1,23), date(2025,1,24), 15, folder)
            self.assertEqual(rows, cached)
            ib.reqHistoricalData.assert_called_once()
            self.assertEqual(info["bars"], 2)
            self.assertEqual(ib.reqHistoricalData.call_args.kwargs["whatToShow"], "MIDPOINT")
            write_csv(folder / "bars.csv", rows)
            self.assertEqual(len((folder / "bars.csv").read_text().splitlines()), 3)

    def test_no_data_fails_instead_of_claiming_ready(self):
        ib = Mock()
        ib.reqHistoricalData.return_value = []
        with TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, "No bars"):
            collect_series(ib, SimpleNamespace(conId=123), date(2025,1,23), date(2025,1,24), 1, Path(tmp))

    def test_bad_prices_rejected(self):
        bar = self.bar(datetime(2025,1,23,tzinfo=timezone.utc))
        bar.high = 149
        with self.assertRaises(ValueError):
            serialize_bar(bar)

    def test_partial_session_fails_minute_coverage(self):
        stamp = datetime(2025,1,23,4,tzinfo=timezone.utc)
        context = [serialize_bar(self.bar(stamp))]
        partial = [serialize_bar(self.bar(stamp))]
        report = coverage_report(context, partial, date(2025,1,23), date(2025,1,24))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["missing_minutes"], 14)
        from datetime import timedelta
        complete = [serialize_bar(self.bar(stamp + timedelta(minutes=i))) for i in range(15)]
        self.assertEqual(coverage_report(context, complete, date(2025,1,23), date(2025,1,24))["status"], "passed")

    def test_minute_requests_use_explicit_four_hour_windows(self):
        stamp = datetime(2025,1,23,4,tzinfo=timezone.utc)
        ib = Mock()
        ib.reqHistoricalData.return_value = [self.bar(stamp)]
        with TemporaryDirectory() as tmp:
            collect_series(ib, SimpleNamespace(conId=123), date(2025,1,23), date(2025,1,24), 1,
                           Path(tmp), expected_times={stamp})
        ib.reqHistoricalData.assert_called_once()
        request = ib.reqHistoricalData.call_args.kwargs
        self.assertEqual(request["durationStr"], "14400 S")
        self.assertEqual(request["barSizeSetting"], "1 min")
        self.assertEqual(request["endDateTime"], datetime(2025,1,23,8,tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
