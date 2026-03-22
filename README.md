# **Project Overview: US Tech Equity Portfolio Appraisal**

## **Use Case:**

This project addresses a strategic requirement for a Small-to-Medium Enterprise (SME) that has accumulated significant surplus cash reserves.

### ***The Challenge:***
The Board of Directors has identified five high-growth US tech stocks—driven by the rapid rise of Artificial Intelligence—for potential inclusion in the company's fiscal reserves. However, given the high volatility of the tech sector, a rigorous risk appraisal is required before capital is committed.

### ***The Objectives:***
As the supporting analyst team, we developed this end-to-end data pipeline to:

#### 1. ***Automate Data Collection:*** Streamline the ingestion of real-time market data from the Alpha Vantage API.

#### 2. ***Quantify Risk:*** Calculate critical financial metrics, including 50-day rolling averages and daily returns.

#### 3. ***Enable Diversification:*** Generate a statistical correlation matrix to support Markowitz risk-return analysis.

#### 4. ***Inform Portfolio Allocation Strategy:*** Provide the CFO with a data-driven portfolio proposal for the upcoming Q3 2026 Board presentation.

## **Data Pipeline Solution:**

The solution utilises a Medallion Architecture to ensure data is progressively refined and validated before reaching the analytics layer.

![Medallion Data Architecture](./medallion_architecture.png)

### ***Pipeline Orchestration (Dagster)***
The entire workflow is orchestrated via Dagster, ensuring a reliable, scheduled, and observable data flow.

### ***Medallion Architecture***

#### 1. ***Bronze Layer (Raw Ingestion):*** Pulls raw market data directly from the Alpha Vantage API. This layer focuses on high-fidelity ingestion into a stocks.sqlite database.

#### 2. ***Silver Layer (Feature Engineering):*** Transforms raw data into actionable indicators. This includes calculating 50-day rolling moving averages and daily percentage returns.

#### 3. ***Gold Layer (Analytics):*** Computes high-level portfolio metrics and a correlation matrix. This matrix is a critical statistical indicator for Markowitz risk-return analysis and portfolio diversification.

### ***Data Stack***
The project leverages a modern, low-overhead stack designed for reliability and accuracy:

#### 1. ***Data Source:*** Alpha Vantage API (US Real-Time Market Data).
#### 2. ***Orchestration:*** Dagster.
#### 3. ***Storage:*** SQLite (stocks.sqlite).
#### 4. ***Data Quality:*** Great Expectations (GX).
#### 5. ***Analytics App:*** Streamlit (Portfolio Simulator Dashboard).
#### 6. ***Database Management:*** DbGate.

### ***Data Quality Assurance (Great Expectations)***
To support high-stakes investment decisions, the pipeline implements a ***"Validate First, Then Materialize"*** strategy using Great Expectations (GX) quality gates at every tier.

### ***Quality Gate Rationales***

#### ***Gate 1 (Schema Validation):*** Ensures the "close" price column contains no null values, as missing data would compromise return calculations. It also verifies that "volume" figures are non-negative to flag anomalous API data.

#### ***Gate 2 (Feature Verification):*** Confirms the successful insertion and existence of engineered features (return_pct and rolling_50) required for trend-spotting.

#### ***Gate 3 (Statistical Integrity):*** Validates that all pairwise correlations in the Gold layer remain within the mathematically sound limit of (-1, 1). This ensures the integrity of the risk-reduction analysis presented to the Board.

### ***Automated Reporting & Monitoring***
The system includes an automated SMTP notification service. Following each daily refresh, the pipeline sends a summary report detailing:

#### 1. *Overall Pipeline Status:* Success/Failure
#### 2. *GX Validation Summary:*  Number of expectations evaluated and success percentage.
#### 3. *Gold Layer record counts:* For final verification.