import os
import sqlite3
import smtplib
import pandas as pd
import great_expectations as gx
from email.message import EmailMessage
from datetime import datetime
from dagster import asset, Definitions, ScheduleDefinition, define_asset_job, AssetSelection, AssetExecutionContext, MetadataValue

# Import specific core objects for GX 0.18.2 compatibility
from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.core.expectation_suite import ExpectationSuite

from src.data import AlphaVantageAPI, SQLRepository
from src.config import settings
from src.logic import process_rolling_metrics, calculate_portfolio_metrics

# --- 1. UTILITY: EMAIL TRIGGER ---
def send_daily_report(success_status, validation_summary):
    msg = EmailMessage()
    msg["Subject"] = f"🚀 Portfolio Refresh {datetime.now().strftime('%Y-%m-%d')}: {success_status}"
    msg["From"] = settings.email_user
    msg["To"] = settings.email_receiver

    body = f"""
    Daily Stock Data Quality Report
    -------------------------
    Overall Status: {success_status}
    Timestamp: {datetime.now()}
    
    Validation Summary:
    {validation_summary}
    
    Check the Dagster UI for detailed execution logs and metadata.
    """
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(settings.email_user, settings.email_password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- 2. UTILITY: GX GATEKEEPER ---
def run_gx_gate(df, suite_name, expectations_configs):
    context = gx.get_context()
    ds_name = f"ds_{suite_name}_{int(datetime.now().timestamp())}"
    
    datasource = context.sources.add_pandas(name=ds_name)
    asset_gx = datasource.add_dataframe_asset(name="current_batch")
    
    suite = ExpectationSuite(expectation_suite_name=suite_name)
    suite.add_expectation_configurations(expectations_configs)
    context.add_expectation_suite(expectation_suite=suite)
        
    validator = context.get_validator(
        batch_request=asset_gx.build_batch_request(dataframe=df),
        expectation_suite_name=suite_name
    )
    return validator.validate()

# --- 3. ASSETS ---

@asset(group_name="Bronze_Layer")
def bronze_layer(context: AssetExecutionContext):
    """BRONZE: Raw Ingestion and Schema Validation."""
    av = AlphaVantageAPI()
    conn = sqlite3.connect(settings.db_name)
    repo = SQLRepository(conn)
    
    failed_tickers = []
    for t in settings.tickers:
        df = av.get_daily(t)
        if not df.empty:
            configs = [
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_not_be_null",
                    kwargs={"column": "close"}
                ),
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_between",
                    kwargs={"column": "volume", "min_value": 0}
                )
            ]
            res = run_gx_gate(df, f"bronze_{t}", configs)
            if res.success:
                repo.insert_table(f"BRONZE_{t}", df)
            else:
                failed_tickers.append(t)
    
    conn.close()
    
    if failed_tickers:
        raise Exception(f"Bronze Layer Incomplete. GX Validation failed for: {', '.join(failed_tickers)}")
    
    return True

@asset(group_name="Silver_Layer")
def silver_layer(context: AssetExecutionContext, bronze_layer: bool):
    """SILVER: Transformation and Quality Validation."""
    conn = sqlite3.connect(settings.db_name)
    repo = SQLRepository(conn)    
    expected_features = ["return_pct", "rolling_50"]	
    failed_tickers = []
    for t in settings.tickers:
        try:
            raw_df = pd.read_sql(f"SELECT * FROM BRONZE_{t}", conn)
            silver_df = process_rolling_metrics(raw_df)
            
            configs = [
                ExpectationConfiguration(
                    expectation_type="expect_column_to_exist",
                    kwargs={"column": feature}
                ) for feature in expected_features
            ]
            res = run_gx_gate(silver_df, f"silver_{t}", configs)
            if res.success:
                repo.insert_table(f"SILVER_{t}", silver_df)
            else:
                failed_tickers.append(t)
        except Exception as e:
            context.log.warning(f"Error processing {t}: {e}")
            failed_tickers.append(t)
    
    conn.close()
    
    if failed_tickers:
        summary = f"Silver Quality Gate Failed for tickers: {', '.join(failed_tickers)}"
        send_daily_report("FAILED", summary)
        raise Exception(summary)
    
    return True

@asset(group_name="Gold_Layer")
def gold_layer(context: AssetExecutionContext, silver_layer: bool):
    """GOLD: Portfolio Statistical Validation and Final Email Trigger."""
    conn = sqlite3.connect(settings.db_name)
    repo = SQLRepository(conn)
    
    all_stocks_dict = {}
    for t in settings.tickers:
        try:
            all_stocks_dict[t] = pd.read_sql(f"SELECT * FROM SILVER_{t}", conn)
        except Exception as e:
            context.log.error(f"Could not load SILVER_{t}: {e}")

    # FIX 1: Pass the first ticker as a string to avoid 'unhashable type: list'
    benchmark_ticker = settings.tickers[0]
    report_df = calculate_portfolio_metrics(all_stocks_dict, benchmark_ticker)
    
    # FIX 2: Select only numeric columns to avoid "could not convert string to float"
    corr_matrix = report_df.select_dtypes(include=['number']).corr()

    configs = [
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={"column": c, "min_value": -1.0001, "max_value": 1.0001}
        ) for c in corr_matrix.columns
    ]
    
    res = run_gx_gate(corr_matrix, "gold_stat_gate", configs)
    status = "SUCCESS" if res.success else "FAILED"
    
    if res.success:
        repo.insert_table("GOLD_PORTFOLIO_METRICS", report_df)

    summary = (
        f"Medallion Pipeline Status: {status}\n"
        f"Expectations Evaluated: {res.statistics['evaluated_expectations']}\n"
        f"Success Percentage: {res.statistics['success_percent']}%\n"
        f"Gold Layer Records: {len(report_df)}"
    )
    
    context.add_output_metadata({
        "success_percent": MetadataValue.float(res.statistics['success_percent']),
        "records_processed": MetadataValue.int(len(report_df))
    })

    send_daily_report(status, summary)
    conn.close()

    if not res.success:
        raise Exception(f"Gold statistical validation failed with {res.statistics['success_percent']}% success.")
        
    return True

# --- 4. DEPLOYMENT ---

portfolio_job = define_asset_job(name="portfolio_refresh_job", selection=AssetSelection.all())

defs = Definitions(
    assets=[bronze_layer, silver_layer, gold_layer],
    schedules=[
        ScheduleDefinition(
            job=portfolio_job,
            cron_schedule="00 6 * * 1-6", 
            execution_timezone="Asia/Singapore"
        )
    ]
)