# System Architecture

The AI-Powered Financial Intelligence Engine follows a clean, modular, and layered architecture designed for maintainability and testability.

## Layers

1. **Domain Models (`backend/models`)**: Built using Pydantic, these models ensure strict type hinting and data validation for incoming Client Profiles and Financial Goals.
2. **Financial Utilities (`backend/utils`)**: Pure mathematical functions for Future Value (FV) and Systematic Investment Plan (SIP) computations. Uncoupled from any specific business context.
3. **Core Engines (`backend/engines`)**: The business logic layer containing Risk Scoring, Goal Computation, Asset Allocation mapping, and Monte Carlo scenario generation.
4. **API Layer (`backend/main.py`)**: Uses FastAPI to expose the backend functionalities over standard REST /api/ endpoints.
5. **Presentation Layer (`frontend/`)**: A Streamlit application rendering interactive UI components like dashboards, forms, and Plotly charts.
6. **Reporting Layer (`backend/report`)**: Jinja2 HTML templates combined with WeasyPrint to generate professional downloadable PDF PDFs.
