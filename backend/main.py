from fastapi import FastAPI, HTTPException
from backend.models.client_model import ClientModel
from backend.models.goal_model import GoalModel
from backend.engines.risk_engine import calculate_risk_score
from backend.engines.goal_engine import (
    calculate_retirement_goal,
    calculate_child_education_goal,
)
from backend.engines.allocation_engine import get_asset_allocation
from backend.engines.monte_carlo_engine import run_monte_carlo_simulation
from pydantic import BaseModel

app = FastAPI(title="AI-Powered Financial Intelligence Engine API")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Financial Intelligence Engine is running"}


@app.post("/api/risk-profile")
def get_risk_profile(client: ClientModel):
    try:
        return calculate_risk_score(
            age=client.age,
            dependents=client.dependents,
            behavior=client.behavior_traits,
            monthly_income=client.monthly_income,
            monthly_savings=client.monthly_savings_capacity,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RetirementRequest(BaseModel):
    current_age: int
    current_monthly_expense: float
    expected_return_rate: float


@app.post("/api/goal/retirement")
def evaluate_retirement(req: RetirementRequest):
    return calculate_retirement_goal(
        req.current_age, req.current_monthly_expense, req.expected_return_rate
    )


class EducationRequest(BaseModel):
    present_cost: float
    years_to_goal: int
    expected_return_rate: float


@app.post("/api/goal/education")
def evaluate_education(req: EducationRequest):
    return calculate_child_education_goal(
        req.present_cost, req.years_to_goal, req.expected_return_rate
    )


@app.get("/api/allocation")
def get_allocation(risk_score: float):
    return get_asset_allocation(risk_score)
