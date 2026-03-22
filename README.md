Project Overview: US Tech Equity Portfolio Appraisal
Use Case
This project addresses a strategic requirement for a Small-to-Medium Enterprise (SME) that has accumulated significant surplus cash reserves. With the rapid rise of Artificial Intelligence, the Board has identified five high-growth US tech stocks for potential investment.

As part of the analyst team, this end-to-end data pipeline was developed to facilitate the Treasury Team’s appraisal of market risks. The goal is to provide the CFO with a risk-aware, data-driven portfolio proposal for the upcoming Board presentation in Q3 2026.
+1

Data Pipeline Solution
The solution utilizes a Medallion Architecture to ensure data is progressively refined and validated before reaching the analytics layer.

Pipeline Orchestration (Dagster)
The entire workflow is orchestrated via Dagster, ensuring a reliable, scheduled, and observable data flow.


(Note: Refer to the orchestration asset graph for the visual relationship between Bronze, Silver, and Gold layers).

Medallion Architecture
Bronze Layer (Raw Ingestion): Pulls raw market data directly from the Alpha Vantage API. This layer focuses on high-fidelity ingestion into a stocks.sqlite database.

Silver Layer (Feature Engineering): Transforms raw data into actionable indicators. This includes calculating 50-day rolling moving averages and daily percentage returns.
+1

Gold Layer (Analytics): Computes high-level portfolio metrics and a correlation matrix. This matrix is a critical statistical indicator for Markowitz risk-return analysis and portfolio diversification.
+2

Data Stack
The project leverages a modern, low-overhead stack designed for reliability and accuracy:


Data Source: Alpha Vantage API (US Real-Time Market Data).


Orchestration: Dagster.


Storage: SQLite (stocks.sqlite).


Data Quality: Great Expectations (GX).
+1


Analytics App: Streamlit (Portfolio Simulator Dashboard).


Database Management: DbGate.

Data Quality Assurance (Great Expectations)
To support high-stakes investment decisions, the pipeline implements a "Validate First, Then Materialize" strategy using Great Expectations (GX) quality gates at every tier.
+1

Quality Gate Rationales
Gate 1 (Schema Validation): Ensures the "close" price column contains no null values, as missing data would compromise return calculations. It also verifies that "volume" figures are non-negative to flag anomalous API data.


Gate 2 (Feature Verification): Confirms the successful insertion and existence of engineered features (return_pct and rolling_50) required for trend-spotting.

Gate 3 (Statistical Integrity): Validates that all pairwise correlations in the Gold layer remain within the mathematically sound limit of (-1, 1). This ensures the integrity of the risk-reduction analysis presented to the Board.
+1

Automated Reporting & Monitoring
The system includes an automated SMTP notification service. Following each daily refresh, the pipeline sends a summary report detailing:

Overall Pipeline Status (Success/Failure).

GX Validation Summary (Number of expectations evaluated and success percentage).

Gold Layer record counts for final verification.