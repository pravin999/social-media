"""Unit tests for snap.py: FIFO matching, aggregates, cross-tabs."""

from __future__ import annotations

import unittest
from typing import Any, Dict, List

from desk.snap import _setup_label, compute_snapshot


class TestSetupLabel(unittest.TestCase):
    """Test setup label extraction from algo_id."""
    
    def test_gex(self):
        self.assertEqual(_setup_label("GEX_STRATEGY"), "GEX")
        self.assertEqual(_setup_label("gex_stock"), "GEX")
    
    def test_vwap(self):
        self.assertEqual(_setup_label("VWAP_STRATEGY"), "VWAP")
        self.assertEqual(_setup_label("vwap_md_long"), "VWAP")
    
    def test_iwm(self):
        self.assertEqual(_setup_label("IWM_CALENDAR"), "IWM")
    
    def test_wish(self):
        self.assertEqual(_setup_label("WISH_QQQ_CALL"), "WISH")
    
    def test_rsi(self):
        self.assertEqual(_setup_label("RSI_STRATEGY"), "RSI")
    
    def test_tv(self):
        self.assertEqual(_setup_label("TV_ALERTS"), "TV")
    
    def test_other(self):
        self.assertEqual(_setup_label("UNKNOWN"), "UNKNOWN")
        self.assertEqual(_setup_label(""), "OTHER")
        self.assertEqual(_setup_label(None), "OTHER")


class TestFIFOMatching(unittest.TestCase):
    """Test FIFO trade matching logic."""
    
    def test_simple_long_win(self):
        """Simple long entry + exit with profit."""
        events = [
            {
                "ts": 1000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
                "price": 100.0, "qty": 10, "algo_id": "VWAP", "ok": True
            },
            {
                "ts": 2000.0, "symbol": "AAPL", "action": "exit", "side": "sell",
                "price": 110.0, "qty": 10, "algo_id": "VWAP", "ok": True
            }
        ]
        
        snap = compute_snapshot(events)
        
        self.assertEqual(snap["n"], 1)
        self.assertAlmostEqual(snap["total_pnl"], 100.0)
        self.assertEqual(snap["wins"], 1)
        self.assertAlmostEqual(snap["win_rate"], 100.0)
        self.assertEqual(len(snap["equity"]), 1)
        self.assertAlmostEqual(snap["equity"][0], 100.0)
    
    def test_simple_short_win(self):
        """Simple short entry + exit with profit."""
        events = [
            {
                "ts": 1000.0, "symbol": "TSLA", "action": "entry", "side": "sell",
                "price": 200.0, "qty": 5, "algo_id": "GEX", "ok": True
            },
            {
                "ts": 2000.0, "symbol": "TSLA", "action": "exit", "side": "buy",
                "price": 180.0, "qty": 5, "algo_id": "GEX", "ok": True
            }
        ]
        
        snap = compute_snapshot(events)
        
        self.assertEqual(snap["n"], 1)
        self.assertAlmostEqual(snap["total_pnl"], 100.0)  # (200 - 180) * 5
        self.assertEqual(snap["wins"], 1)
    
    def test_long_loss(self):
        """Long trade with loss."""
        events = [
            {
                "ts": 1000.0, "symbol": "NVDA", "action": "entry", "side": "buy",
                "price": 500.0, "qty": 2, "algo_id": "VWAP", "ok": True
            },
            {
                "ts": 2000.0, "symbol": "NVDA", "action": "exit", "side": "sell",
                "price": 480.0, "qty": 2, "algo_id": "VWAP", "ok": True
            }
        ]
        
        snap = compute_snapshot(events)
        
        self.assertEqual(snap["n"], 1)
        self.assertAlmostEqual(snap["total_pnl"], -40.0)  # (480 - 500) * 2
        self.assertEqual(snap["wins"], 0)
        self.assertAlmostEqual(snap["win_rate"], 0.0)
    
    def test_multiple_trades_fifo(self):
        """Multiple trades, FIFO matching."""
        events = [
            # Entry 1
            {"ts": 1000.0, "symbol": "SMCI", "action": "entry", "side": "buy",
             "price": 20.0, "qty": 10, "algo_id": "GEX", "ok": True},
            # Entry 2
            {"ts": 1500.0, "symbol": "SMCI", "action": "entry", "side": "buy",
             "price": 22.0, "qty": 5, "algo_id": "GEX", "ok": True},
            # Exit matches Entry 1 (FIFO)
            {"ts": 2000.0, "symbol": "SMCI", "action": "exit", "side": "sell",
             "price": 25.0, "qty": 10, "algo_id": "GEX", "ok": True},
            # Exit matches Entry 2
            {"ts": 2500.0, "symbol": "SMCI", "action": "exit", "side": "sell",
             "price": 24.0, "qty": 5, "algo_id": "GEX", "ok": True}
        ]
        
        snap = compute_snapshot(events)
        
        self.assertEqual(snap["n"], 2)
        # Trade 1: (25 - 20) * 10 = 50
        # Trade 2: (24 - 22) * 5 = 10
        # Total: 60
        self.assertAlmostEqual(snap["total_pnl"], 60.0)
        self.assertEqual(snap["wins"], 2)
    
    def test_open_positions(self):
        """Unmatched entries become open positions."""
        events = [
            {"ts": 1000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
             "price": 150.0, "qty": 10, "algo_id": "VWAP", "ok": True},
            {"ts": 1100.0, "symbol": "TSLA", "action": "entry", "side": "sell",
             "price": 250.0, "qty": 5, "algo_id": "GEX", "ok": True}
        ]
        
        snap = compute_snapshot(events)
        
        self.assertEqual(snap["n"], 0)  # No closed trades
        self.assertEqual(len(snap["open_positions"]), 2)
        
        opens = {op["symbol"]: op for op in snap["open_positions"]}
        self.assertIn("AAPL", opens)
        self.assertIn("TSLA", opens)
        self.assertEqual(opens["AAPL"]["side"], "buy")
        self.assertEqual(opens["TSLA"]["side"], "sell")
    
    def test_ignores_not_ok(self):
        """Failed events (ok=False) are ignored."""
        events = [
            {"ts": 1000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
             "price": 100.0, "qty": 10, "algo_id": "VWAP", "ok": False},
            {"ts": 2000.0, "symbol": "AAPL", "action": "exit", "side": "sell",
             "price": 110.0, "qty": 10, "algo_id": "VWAP", "ok": True}
        ]
        
        snap = compute_snapshot(events)
        
        self.assertEqual(snap["n"], 0)  # No match because entry failed


class TestAggregates(unittest.TestCase):
    """Test KPI aggregations."""
    
    def test_by_setup(self):
        """Aggregate PnL by setup."""
        events = [
            {"ts": 1000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
             "price": 100.0, "qty": 10, "algo_id": "VWAP_STRATEGY", "ok": True},
            {"ts": 2000.0, "symbol": "AAPL", "action": "exit", "side": "sell",
             "price": 110.0, "qty": 10, "algo_id": "VWAP_STRATEGY", "ok": True},
            
            {"ts": 3000.0, "symbol": "TSLA", "action": "entry", "side": "sell",
             "price": 200.0, "qty": 5, "algo_id": "GEX_STOCK", "ok": True},
            {"ts": 4000.0, "symbol": "TSLA", "action": "exit", "side": "buy",
             "price": 180.0, "qty": 5, "algo_id": "GEX_STOCK", "ok": True}
        ]
        
        snap = compute_snapshot(events)
        
        by_setup = snap["by_setup"]
        self.assertIn("VWAP", by_setup)
        self.assertIn("GEX", by_setup)
        
        self.assertAlmostEqual(by_setup["VWAP"]["pnl"], 100.0)
        self.assertEqual(by_setup["VWAP"]["n"], 1)
        self.assertEqual(by_setup["VWAP"]["wins"], 1)
        
        self.assertAlmostEqual(by_setup["GEX"]["pnl"], 100.0)
        self.assertEqual(by_setup["GEX"]["n"], 1)
    
    def test_by_ticker(self):
        """Aggregate PnL by ticker."""
        events = [
            {"ts": 1000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
             "price": 100.0, "qty": 10, "algo_id": "VWAP", "ok": True},
            {"ts": 2000.0, "symbol": "AAPL", "action": "exit", "side": "sell",
             "price": 105.0, "qty": 10, "algo_id": "VWAP", "ok": True},
            
            {"ts": 3000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
             "price": 105.0, "qty": 5, "algo_id": "GEX", "ok": True},
            {"ts": 4000.0, "symbol": "AAPL", "action": "exit", "side": "sell",
             "price": 110.0, "qty": 5, "algo_id": "GEX", "ok": True}
        ]
        
        snap = compute_snapshot(events)
        
        by_ticker = snap["by_ticker"]
        self.assertIn("AAPL", by_ticker)
        
        # Trade 1: (105 - 100) * 10 = 50
        # Trade 2: (110 - 105) * 5 = 25
        # Total: 75
        self.assertAlmostEqual(by_ticker["AAPL"]["pnl"], 75.0)
        self.assertEqual(by_ticker["AAPL"]["n"], 2)
        self.assertEqual(by_ticker["AAPL"]["wins"], 2)
    
    def test_by_setup_ticker_crosstab(self):
        """Cross-tab: setup × ticker."""
        events = [
            {"ts": 1000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
             "price": 100.0, "qty": 10, "algo_id": "VWAP", "ok": True},
            {"ts": 2000.0, "symbol": "AAPL", "action": "exit", "side": "sell",
             "price": 110.0, "qty": 10, "algo_id": "VWAP", "ok": True},
            
            {"ts": 3000.0, "symbol": "TSLA", "action": "entry", "side": "buy",
             "price": 200.0, "qty": 5, "algo_id": "VWAP", "ok": True},
            {"ts": 4000.0, "symbol": "TSLA", "action": "exit", "side": "sell",
             "price": 190.0, "qty": 5, "algo_id": "VWAP", "ok": True},
            
            {"ts": 5000.0, "symbol": "AAPL", "action": "entry", "side": "sell",
             "price": 110.0, "qty": 10, "algo_id": "GEX", "ok": True},
            {"ts": 6000.0, "symbol": "AAPL", "action": "exit", "side": "buy",
             "price": 100.0, "qty": 10, "algo_id": "GEX", "ok": True}
        ]
        
        snap = compute_snapshot(events)
        
        cross = snap["by_setup_ticker"]
        
        self.assertIn("VWAP", cross)
        self.assertIn("GEX", cross)
        
        # VWAP × AAPL: +100
        self.assertAlmostEqual(cross["VWAP"]["AAPL"], 100.0)
        # VWAP × TSLA: -50
        self.assertAlmostEqual(cross["VWAP"]["TSLA"], -50.0)
        # GEX × AAPL: +100
        self.assertAlmostEqual(cross["GEX"]["AAPL"], 100.0)


class TestEquityCurve(unittest.TestCase):
    """Test equity curve generation."""
    
    def test_equity_curve(self):
        """Equity curve tracks running PnL."""
        events = [
            {"ts": 1000.0, "symbol": "AAPL", "action": "entry", "side": "buy",
             "price": 100.0, "qty": 10, "algo_id": "VWAP", "ok": True},
            {"ts": 2000.0, "symbol": "AAPL", "action": "exit", "side": "sell",
             "price": 110.0, "qty": 10, "algo_id": "VWAP", "ok": True},
            
            {"ts": 3000.0, "symbol": "TSLA", "action": "entry", "side": "buy",
             "price": 200.0, "qty": 5, "algo_id": "GEX", "ok": True},
            {"ts": 4000.0, "symbol": "TSLA", "action": "exit", "side": "sell",
             "price": 190.0, "qty": 5, "algo_id": "GEX", "ok": True}
        ]
        
        snap = compute_snapshot(events)
        
        eq = snap["equity"]
        self.assertEqual(len(eq), 2)
        self.assertAlmostEqual(eq[0], 100.0)  # After trade 1
        self.assertAlmostEqual(eq[1], 50.0)   # After trade 2 (100 - 50)
    
    def test_equity_downsampling(self):
        """Equity curve downsamples to max 100 points."""
        # Create 200 trades
        events: List[Dict[str, Any]] = []
        for i in range(200):
            events.append({
                "ts": 1000.0 + i * 10, "symbol": "AAPL", "action": "entry",
                "side": "buy", "price": 100.0, "qty": 1, "algo_id": "VWAP", "ok": True
            })
            events.append({
                "ts": 1005.0 + i * 10, "symbol": "AAPL", "action": "exit",
                "side": "sell", "price": 101.0, "qty": 1, "algo_id": "VWAP", "ok": True
            })
        
        snap = compute_snapshot(events)
        
        self.assertEqual(snap["n"], 200)
        # Equity should be downsampled to 100 points
        self.assertLessEqual(len(snap["equity"]), 100)


if __name__ == "__main__":
    unittest.main()
