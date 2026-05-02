import pytest
from unittest.mock import patch, MagicMock

from src.agents.portfolio_health import _analyse_portfolio, DISCLAIMER

class TestPortfolioHealthAnalysis:
    def test_empty_portfolio_does_not_crash(self):
        """user_004_empty — must produce BUILD-oriented response."""
        result = _analyse_portfolio([], {"currency": "USD", "country": "US", "risk_profile": "moderate"})
        assert result is not None
        assert result.is_empty_portfolio is True
        assert len(result.observations) > 0
        assert result.disclaimer == DISCLAIMER
        # Must contain BUILD-oriented guidance
        obs_text = " ".join(o.text for o in result.observations).lower()
        assert any(word in obs_text for word in ["start", "first", "begin", "index", "etf"])
    
    def test_concentrated_portfolio_flags_risk(self):
        holdings = [
            {"ticker": "NVDA", "quantity": 100, "avg_cost": 400.0, "current_value": 80000.0},
            {"ticker": "AAPL", "quantity": 10, "avg_cost": 150.0, "current_value": 1500.0},
        ]
        with patch("src.agents.portfolio_health._fetch_current_prices", return_value={}):
            with patch("src.agents.portfolio_health._fetch_benchmark_return", return_value=14.0):
                result = _analyse_portfolio(holdings, {"currency": "USD", "country": "US"})
        
        assert result.concentration_risk.flag in ["high", "critical"]
        assert result.concentration_risk.top_position_pct > 50
        # Should have a warning/critical observation
        severity_flags = [o.severity for o in result.observations]
        assert any(s in ["warning", "critical"] for s in severity_flags)
    
    def test_disclaimer_always_present(self):
        holdings = [{"ticker": "AAPL", "quantity": 10, "avg_cost": 150.0, "current_value": 1700.0}]
        with patch("src.agents.portfolio_health._fetch_current_prices", return_value={}):
            with patch("src.agents.portfolio_health._fetch_benchmark_return", return_value=14.0):
                result = _analyse_portfolio(holdings, {"currency": "USD", "country": "US"})
        assert result.disclaimer is not None
        assert len(result.disclaimer) > 0
    
    def test_benchmark_selected_for_indian_user(self):
        holdings = [{"ticker": "RELIANCE.NS", "quantity": 10, "avg_cost": 2000.0, "current_value": 25000.0}]
        with patch("src.agents.portfolio_health._fetch_current_prices", return_value={}):
            with patch("src.agents.portfolio_health._fetch_benchmark_return", return_value=12.0):
                result = _analyse_portfolio(holdings, {"currency": "INR", "country": "IN"})
        assert "Nifty" in result.benchmark_comparison.benchmark
    
    def test_performance_calculated_correctly(self):
        holdings = [
            {"ticker": "AAPL", "quantity": 10, "avg_cost": 100.0, "current_value": 1200.0}
        ]
        # cost_basis = 10 * 100 = 1000, current_value = 1200, return = 20%
        with patch("src.agents.portfolio_health._fetch_current_prices", return_value={}):
            with patch("src.agents.portfolio_health._fetch_benchmark_return", return_value=14.0):
                result = _analyse_portfolio(holdings, {"currency": "USD", "country": "US"})
        assert result.performance.total_return_pct == pytest.approx(20.0, abs=0.1)
