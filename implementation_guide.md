# **Implementation Guide**

This guide will walk you through setting up the automated data pipeline, launching the interactive analytics dashboard and running backend custom analytics with either SQL or Python.

## **Project Architecture**

This project utilizes a Medallion Architecture (Bronze, Silver, Gold layers) to ensure data integrity and sophisticated financial modeling.

```
├── src/
│   ├── config.py          # Centralized settings & environment loader
│   ├── data.py            # API & SQL Repository classes
│   └── logic.py           # Portfolio metrics & calculation engine
├── .env.example           # Template for required API keys & credentials
├── app_v1.py              # Streamlit dashboard & strategy simulator
├── definitions_v1.py      # Dagster orchestration & quality gates
└── requirements.txt       # Project dependencies
```

## **Step 1: Local Environment Setup**

***Clone the Repository:***

Bash
```
git clone https://github.com/lowlinus178/NTU_DSAI_Module2_Capstone.git
cd <your local target folder>
```

***Install Dependencies:***

It is recommended to use Python 3.11+.

Bash
```
pip install -r requirements.txt
```

***Configure Secrets:***

Create a .env file in the root directory. This project requires an Alpha Vantage API key and Gmail SMTP credentials for automated reporting.

Code snippet
```
ALPHAVANTAGE_API_KEY=your_api_key_here
DB_NAME="stocks.sqlite" 
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=target_recipient@gmail.com
```

## **Step 2: Data Orchestration (Dagster)**

The pipeline automates data ingestion, transformation, and validation.

***1. Launch the Orchestrator:***

Bash
```
dagster dev -f definitions_v1.py
```

***2. Materialize Assets:***

* Open http://localhost:3000 in your browser.

* Navigate to Assets and click ***Materialize All***.

* ***Note:*** The first run will automatically create the ***stocks.sqlite*** DB file in your root directory.


***3. Data Quality Gates:***

This project integrates Great Expectations (GX) to prevent "garbage-in, garbage-out":

***Bronze:*** Validates raw API responses for null values.

***Silver:*** Ensures engineered features exist before storage.

***Gold:*** Validates the statistical integrity of the correlation matrix.

### ***Step 3: Launching the Streamlit Dashboard***

Once the data pipeline has finished (Gold layer is green), you can view the insights.

Bash
```
streamlit run app_v1.py
```

***Dashboard Features:***

***Market Review:*** View 50-day Moving Average trends and daily price movements.

***Risk Analytics:*** Compare Alpha, Beta, and Sharpe Ratios against benchmarks (SPY/QQQ).

***Portfolio Allocation Simulator:***  A "What-If" tool to adjust asset weights and witness the Volatility Reduction Effect in real-time.

### ***Step 4: Performing backend ad hoc SQL analytics and query***

Once the pipeline has populated the ***stocks.sqlite*** DB, you can perform ad hoc analysis using the following methods:

***Method A: User-Friendly GUI (DBGate)***

For those who prefer a visual SQL editor:

1. Open DBGate (or any SQLite-compatible browser).

2. Select SQLite as the database type.

3. Point the application to the ***stocks.sqlite*** DB file in your project root.

4. Run ***standard SQL queries*** against the Silver/Gold Medallion tables.

***Method B: Programmatic Access (SQLAlchemy / Pandas)***

If you are working in a Jupyter Notebook or a Python script, you can load the data directly into a DataFrame using SQLAlchemy:

Python
```
import pandas as pd
from sqlalchemy import create_all_engine

# 1. Create the connection string
engine = create_all_engine("sqlite:///stocks.sqlite")

# 2. Read from the Gold or Silver layers
df = pd.read_sql("SELECT * FROM <Table Name>", con=engine)

# 3. Perform ad hoc analysis with Pandas
```

## **3. Maintenance & Scheduling**

* ***Automated Reports:*** A daily status report is sent to the configured email at 6:00 AM SGT (Mon-Sat).

* ***Local SQLite DB:*** The stocks.sqlite DB file is excluded from version control to keep the repository clean. It is refreshed every time the pipeline runs.