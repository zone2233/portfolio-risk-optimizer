"""Offline tests for UI boundaries; no backend code or formula is replaced on disk."""

from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest


APP = str(Path(__file__).resolve().parents[1] / "app.py")


def asset_data(ticker, start, end):
    # Isolated UI fixture, never used by app.py as a data fallback.
    return pd.DataFrame({ticker: [0.01, -0.02, 0.005]},
                        index=pd.date_range("2025-01-01", periods=3))


class FrontendTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()

    def app(self):
        app = AppTest.from_file(APP, default_timeout=15).run()
        self.assertEqual(len(app.exception), 0)
        return app

    def submit(self, app):
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_initial_screen_does_not_download_or_import_analysis(self):
        with patch("data_loader.get_return") as loader:
            app = self.app()
        loader.assert_not_called()
        self.assertEqual(app.title[0].value, "Portfolio Risk Optimizer")
        self.assertEqual([input.value for input in app.text_input], ["SPY", "GLD"])
        self.assertEqual(len(app.metric), 0)
        self.assertIn("analysis.py", app.info[0].value)

    def test_invalid_tickers_do_not_call_backend(self):
        for first, second, message in [
            ("", "GLD", "Enter a ticker"),
            ("spy", " SPY ", "two different"),
            ("<script>", "GLD", "valid ticker"),
        ]:
            with self.subTest(first=first), patch("data_loader.get_return") as loader:
                app = self.app()
                app.text_input[0].set_value(first)
                app.text_input[1].set_value(second)
                self.submit(app)
                self.assertIn(message, app.error[0].value)
                loader.assert_not_called()

    def test_real_optimizer_error_is_actionable_and_data_is_cached(self):
        with patch("data_loader.get_return", side_effect=asset_data) as loader:
            app = self.submit(self.app())
            self.assertIn("omit the ticker arguments", app.error[0].value)
            self.assertEqual(len(app.metric), 0)
            self.submit(app)
            self.assertEqual(loader.call_count, 2)

    def test_loader_failure_is_displayed(self):
        with patch("data_loader.get_return", side_effect=ValueError("No data found for SPY")):
            app = self.submit(self.app())
        self.assertIn("No data found", app.error[0].value)
        self.assertEqual(len(app.metric), 0)

    def test_nonoverlapping_and_nonfinite_returns_are_rejected(self):
        for data, message in [
            (pd.DataFrame({"SPY": [], "GLD": []}), "Not enough overlapping"),
            (pd.DataFrame({"SPY": [float("inf"), 0.1], "GLD": [0.1, 0.2]}), "non-finite"),
        ]:
            with self.subTest(message=message), \
                 patch("data_loader.get_return", side_effect=asset_data), \
                 patch("data_loader.combine_df", return_value=data), \
                 patch("portfolio_math.min_volatility_weight") as optimizer:
                app = self.submit(self.app())
                self.assertIn(message, app.error[0].value)
                optimizer.assert_not_called()

    def test_backend_results_render_and_failed_submission_clears_them(self):
        def optimizer(returns, ticker1, ticker2):
            self.assertEqual((ticker1, ticker2), ("SPY", "GLD"))
            return 0.37, 0.1234

        with patch("data_loader.get_return", side_effect=asset_data), \
             patch("portfolio_math.min_volatility_weight", new=optimizer):
            app = self.submit(self.app())
            self.assertEqual([metric.value for metric in app.metric],
                             ["37.0%", "63.0%", "12.34%"])
            app.text_input[0].set_value("")
            self.submit(app)
            self.assertEqual(len(app.metric), 0)
            self.assertIn("Enter a ticker", app.error[0].value)

    def test_invalid_backend_result_never_renders(self):
        with patch("data_loader.get_return", side_effect=asset_data), \
             patch("portfolio_math.min_volatility_weight", return_value=(0.5, float("nan"))):
            app = self.submit(self.app())
        self.assertIn("invalid volatility", app.error[0].value)
        self.assertEqual(len(app.metric), 0)


if __name__ == "__main__":
    unittest.main()
