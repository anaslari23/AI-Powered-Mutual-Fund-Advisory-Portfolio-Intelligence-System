import streamlit as st


def render_input_form():
    """Renders the client profile and goals input form."""
    with st.form("client_form"):
        st.subheader("Personal Details")
        age = st.number_input("Age", min_value=18, max_value=100, value=30)
        dependents = st.number_input("Dependents", min_value=0, max_value=10, value=0)

        st.subheader("Financial Details")
        monthly_income = st.number_input(
            "Monthly Income", min_value=0.0, value=100000.0, step=10000.0
        )
        monthly_savings = st.number_input(
            "Monthly Savings Capacity", min_value=0.0, value=30000.0, step=5000.0
        )

        st.subheader("Behavioral Traits")
        behavior_traits = st.selectbox(
            "Market Behavior", ["Prefers stability", "Moderate", "High risk"]
        )

        st.subheader("Financial Goals")
        st.markdown("**Retirement**")
        retirement_expense = st.number_input(
            "Monthly Expense in Retirement (Current Value)",
            min_value=0.0,
            value=50000.0,
            step=5000.0,
        )

        st.markdown("**Child Education**")
        education_cost = st.number_input(
            "Present Cost of Education", min_value=0.0, value=2000000.0, step=100000.0
        )
        education_years = st.number_input(
            "Years to Education Goal", min_value=1, max_value=25, value=12
        )

        submitted = st.form_submit_button("Generate Financial Plan")

        if submitted:
            if monthly_savings > monthly_income:
                st.error("Savings cannot exceed income.")
            else:
                st.session_state.client_data = {
                    "age": age,
                    "dependents": dependents,
                    "monthly_income": monthly_income,
                    "monthly_savings": monthly_savings,
                    "behavior": behavior_traits,
                    "goals": {
                        "retirement": {"expense": retirement_expense},
                        "education": {"cost": education_cost, "years": education_years},
                    },
                }
