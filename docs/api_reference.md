# API Reference

The FastAPI backend exposes the following endpoints:

- `GET /` : Health check.
- `POST /api/risk-profile`: Expects a complete `ClientModel` JSON and returns the calculated Risk Score (0-10) and Category.
- `POST /api/goal/retirement`: Takes current age, expected monthly retirement expense, and return rate to output required corpus and SIP.
- `POST /api/goal/education`: Takes present cost of education and calculates future corpus and required SIP.
- `GET /api/allocation`: Takes a query parameter `risk_score` and returns the asset allocation split summing tightly to 100%.
