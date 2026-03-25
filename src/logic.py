import pandas as pd 
import numpy as np

def process_rolling_metrics(df):
    """Calculates daily returns and 50-day SMA for a single ticker."""
    # Ensure date is a datetime object for proper sorting
    df['date'] = pd.to_datetime(df['date'])
    
    # FIX: Sort ascending (oldest to newest) before calculating pct_change
    # This ensures today is compared to yesterday, not tomorrow.
    df = df.sort_values('date', ascending=True)
    
    # Calculate daily returns on chronologically ordered data
    df['return_pct'] = df['close'].pct_change()
    
    # Calculate 50-day Simple Moving Average
    df['rolling_50'] = df['close'].rolling(window=50).mean()
    
    return df.dropna()

def calculate_portfolio_metrics(all_stocks_dict, benchmark_ticker="SPY"):
    results = []
    risk_free_rate = 0.04 # 4% Annualized
    
    # Ensure the benchmark ticker exists in the loaded dictionary
    if benchmark_ticker not in all_stocks_dict:
        return pd.DataFrame()
        
    benchmark_df = all_stocks_dict[benchmark_ticker]
    
    for ticker, df in all_stocks_dict.items():
        # Align asset and benchmark on the same dates
        combined = pd.merge(
            df[['return_pct']], 
            benchmark_df[['return_pct']], 
            left_index=True, 
            right_index=True, 
            suffixes=('', '_bench')
        ).dropna()
        
        if combined.empty:
            continue
            
        # Annualized metrics
        ann_return = combined['return_pct'].mean() * 252
        ann_vol = combined['return_pct'].std() * np.sqrt(252)
        
        # Risk Metrics (Beta & Alpha)
        # combined.cov().iloc[0, 1] is Cov(Asset, Benchmark)
        beta = combined.cov().iloc[0, 1] / combined['return_pct_bench'].var()
        bench_ann_return = combined['return_pct_bench'].mean() * 252
        alpha = ann_return - (risk_free_rate + beta * (bench_ann_return - risk_free_rate))
        
        # Sharpe Ratio (Excess return per unit of risk)
        sharpe = (ann_return - risk_free_rate) / ann_vol if ann_vol != 0 else 0
        
        results.append({
            "Ticker": ticker,
            "Latest Price": float(df['close'].iloc[-1]),
            "Ann. Return": float(ann_return),
            "Volatility": float(ann_vol),
            "Beta": float(beta),
            "Alpha": float(alpha),
            "Sharpe Ratio": float(sharpe)
        })
    return pd.DataFrame(results)