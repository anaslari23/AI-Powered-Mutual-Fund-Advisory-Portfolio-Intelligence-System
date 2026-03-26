from backend.engines.investment_mode_engine import recommend_investment_mode


def test_recommends_sip_in_low_stability_market():
    result = recommend_investment_mode(
        {
            "market_stability_score": 0.42,
            "vix_level": 24.0,
            "market_trend": "bearish",
        },
        available_capital=600000,
    )
    assert result["recommended_mode"] == "SIP"
    assert "uncertain" in result["trigger_reason"].lower()


def test_recommends_lumpsum_for_fair_value_stable_market():
    result = recommend_investment_mode(
        {
            "market_stability_score": 0.86,
            "vix_level": 12.0,
            "market_trend": "bullish",
            "nifty_pe": 21.4,
        },
        available_capital=500000,
    )
    assert result["recommended_mode"] == "Lumpsum"
    assert "fair value" in result["trigger_reason"].lower()


def test_recommends_stp_for_large_idle_corpus_in_cautious_market():
    result = recommend_investment_mode(
        {
            "market_stability_score": 0.67,
            "vix_level": 17.5,
            "market_trend": "neutral",
            "nifty_pe": 23.1,
        },
        available_capital=900000,
    )
    assert result["recommended_mode"] == "STP"
    assert "liquid fund" in result["deployment_plan"]
