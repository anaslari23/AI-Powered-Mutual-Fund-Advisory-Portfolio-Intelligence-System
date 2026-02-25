from pydantic import BaseModel, Field, field_validator


class GoalModel(BaseModel):
    """
    Domain model for a Financial Goal.
    """

    goal_name: str = Field(..., description="Name of the financial goal")
    years_to_goal: int = Field(..., description="Years remaining to achieve the goal")
    present_cost: float = Field(
        ..., description="Current cost of the goal in today's value", ge=0
    )
    inflation_rate: float = Field(
        ...,
        description="Expected inflation rate (as a decimal, e.g., 0.06 for 6%)",
        ge=0,
    )

    @field_validator("years_to_goal")
    @classmethod
    def validate_years(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Years to goal must be > 0")
        return v
