class RetirementPlanner:
    @staticmethod
    def calculate_annuity_corpus(
        monthly_income_needed, retirement_age, life_expectancy=85, swr_pct=3.5
    ):
        annual = monthly_income_needed * 12

        corpus = annual / (swr_pct / 100)

        return {
            "required_corpus": round(corpus, 2),
            "retirement_years": life_expectancy - retirement_age,
        }

    @staticmethod
    def generate_swp_plan(corpus, monthly_withdrawal):
        plan = []
        balance = corpus

        for year in range(1, 36):
            balance -= monthly_withdrawal * 12

            plan.append({"year": year, "balance": max(balance, 0)})

            if balance <= 0:
                break

        return plan

    @staticmethod
    def calculate_term_insurance_need(
        annual_income, years_to_retirement, loans=0, corpus=0
    ):
        required = max(annual_income * 10, corpus + loans)

        return {
            "recommended_cover": round(required, -5),
            "tenure": years_to_retirement + 5,
        }


def healthcare_corpus(monthly_cost):
    return monthly_cost * 12 * 20


def spouse_retirement(expenses):
    return expenses * 12 * 25


def fire_calculator(expenses):
    return expenses * 12 * 30


def swp_simulation(corpus, withdrawal):
    return corpus / (withdrawal * 12)


def early_retirement_plan(age, retirement_age, expenses):
    years = retirement_age - age
    corpus = expenses * 12 * 25
    return {"years": years, "target_corpus": corpus}


def phased_retirement_plan(expenses):
    return expenses * 12 * 30


def passive_income_plan(monthly_target):
    return monthly_target * 12 * 20
