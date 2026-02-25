from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, Any

class ClientModel(BaseModel):
    """
    Domain model for a Client's profile.
    """
    age: int = Field(..., description="Age of the client")
    monthly_income: float = Field(..., description="Monthly income in standard currency", ge=0)
    monthly_savings_capacity: float = Field(..., description="Monthly savings capacity", ge=0)
    dependents: int = Field(..., description="Number of dependents", ge=0)
    marital_status: str = Field(..., description="Marital status (e.g., Single, Married)")
    risk_appetite: str = Field(..., description="Self-declared risk appetite")
    behavior_traits: str = Field(..., description="Behavior traits (e.g., Prefers stability, Moderate, High risk)")
    existing_assets: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of existing assets")

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v <= 18:
            raise ValueError("Client age must be > 18")
        return v

    @model_validator(mode="after")
    def validate_savings(self) -> 'ClientModel':
        if self.monthly_savings_capacity > self.monthly_income:
            raise ValueError("Savings capacity cannot exceed monthly income")
        return self
