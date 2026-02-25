# AI-Powered Mutual Fund Advisory & Portfolio Intelligence System

An AI-based Goal-Oriented Financial Planning Engine.

## Features
- Calculates retirement corpus
- Calculates child education corpus
- Recommends SIP allocation
- Computes explainable risk score
- Generates interactive dashboard
- Produces downloadable PDF report
## Architecture Flow

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#ff9900,stroke:#333,stroke-width:2px,color:#000
    classDef backend fill:#00cc66,stroke:#333,stroke-width:2px,color:#fff
    classDef engine fill:#3399ff,stroke:#333,stroke-width:2px,color:#fff
    classDef pdf fill:#ff3366,stroke:#333,stroke-width:2px,color:#fff
    
    %% Components
    UI[Streamlit Frontend Form]:::frontend
    Dash[Interactive UI Dashboard]:::frontend
    API[FastAPI Backend Router]:::backend
    
    Risk[Risk Scoring Engine]:::engine
    Goal[Goal Computation Engine]:::engine
    Alloc[Asset Allocation Engine]:::engine
    MC[Monte Carlo Simulation Engine]:::engine
    
    Report[WeasyPrint PDF Generator]:::pdf
    
    %% Flow
    UI -->|JSON Profile Data| API
    API --> Risk
    API --> Goal
    API --> Alloc
    API --> MC
    
    Risk -->|Score 0-10| Dash
    Goal -->|Required SIP| Dash
    Alloc -->|100% Portfolio| Dash
    MC -->|Success %| Dash
    
    Dash -->|Trigger| Report
    Report -->|Download URL| Dash
```

## Tech Stack
- Backend: FastAPI
- Frontend: Streamlit
- Charts: Plotly
- Math & Data: NumPy, Pandas
- PDF Generation: WeasyPrint

## Disclaimer
Please see `DISCLAIMER.txt`.
