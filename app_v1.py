import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from src.config import settings
from src.logic import calculate_portfolio_metrics

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(layout="wide", page_title="Portfolio Analytics Report", page_icon="📊")

# Refined CSS for readable metrics and professional headers
st.markdown("""
    <style>
    .stMetric { 
        border: 1px solid #4B5563; 
        background-color: #0d1117; 
        padding: 10px; 
        border-radius: 8px; 
    }
    [data-testid="stMetricValue"] { 
        font-weight: 800 !important; 
        color: #00ff88; 
        font-size: 1.4rem !important; 
    }
    h2 { color: #00ff88; border-bottom: 3px solid #00ff88; padding-bottom: 10px; margin-top: 40px; }
    h3 { font-weight: 800; color: #ffffff; border-bottom: 1px solid #374151; padding-bottom: 5px; margin-top: 10px; }
    .simulator-panel { 
        background-color: #0f172a; 
        padding: 25px; 
        border-radius: 15px; 
        border: 2px solid #3b82f6; 
        margin-top: 10px;
    }
    .instruction-text {
        font-size: 0.95rem;
        color: #94a3b8;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Institutional Equity & Risk Analytics")
st.caption("Reporting Period: Last 252 Trading Days • Medallion Architecture")

try:
    # --- 2. DATA INGESTION ---
    conn = sqlite3.connect(settings.db_name)
    # FIX: Added .sort_index(ascending=True) to ensure the latest data is at the end of the DataFrame
    all_data = {
        t: pd.read_sql(f"SELECT * FROM SILVER_{t}", conn)
        .assign(date=lambda x: pd.to_datetime(x['date']))
        .set_index('date')
        .sort_index(ascending=True) 
        for t in settings.tickers
    }

    # =================================================================
    # PART I: HISTORICAL PERFORMANCE REPORTING (STATIC)
    # =================================================================
    st.header("Section I: Historical Market Review")
    
    # 1. Market Component Prices
    st.subheader("Asset Price Snapshot")
    ticker_chunks = [settings.tickers[i:i + 4] for i in range(0, len(settings.tickers), 4)]
    for chunk in ticker_chunks:
        cols = st.columns(4)
        for i, t in enumerate(chunk):
            # With the sorted index, iloc[-1] is now correctly the most recent day
            latest, prev = all_data[t]['close'].iloc[-1], all_data[t]['close'].iloc[-2]
            delta = (latest - prev) / prev
            cols[i].metric(label=f"Ticker: {t}", value=f"${latest:,.2f}", delta=f"{delta:.2%}")

    # 2. Trend Grid
    st.divider()
    st.subheader("Fundamental Price Trends (50-Day Moving Average)")
    stocks_only_list = [t for t in settings.tickers if t not in ["SPY", "QQQ"]]
    for i in range(0, len(stocks_only_list), 3):
        row_cols = st.columns(3)
        for j, ticker in enumerate(stocks_only_list[i:i+3]):
            with row_cols[j]:
                # tail(120) now correctly captures the most recent 120 trading days
                df_p = all_data[ticker].tail(120)
                fig_t = go.Figure([
                    go.Scatter(x=df_p.index, y=df_p['close'], name="Price", line=dict(color='#00ff88', width=2.5)),
                    go.Scatter(x=df_p.index, y=df_p['rolling_50'], name="50D SMA", line=dict(color='#ffcc00', dash='dash'))
                ])
                fig_t.update_layout(title=f"<b>{ticker}</b>", template="plotly_dark", height=230, margin=dict(l=10,r=10,t=40,b=10), showlegend=False)
                st.plotly_chart(fig_t, use_container_width=True)

    # 3. CAPM Risk Metrics
    st.divider()
    st.subheader("Standalone Risk & Alpha Analysis (Annualized)")
    risk_report = calculate_portfolio_metrics(all_data, benchmark_ticker="SPY")
    spy_val = risk_report.query("Ticker=='SPY'").iloc[0]
    qqq_val = risk_report.query("Ticker=='QQQ'").iloc[0]
    stocks_report = risk_report[~risk_report['Ticker'].isin(['SPY', 'QQQ'])]

    def quick_bar(df, col, title, spy, qqq):
        fig = px.bar(df, x='Ticker', y=col, title=f"<b>{title}</b>", template="plotly_dark", color=col, color_continuous_scale="Turbo")
        fig.add_hline(y=spy, line_dash="dash", line_color="#FF4B4B", annotation_text="SPY")
        fig.add_hline(y=qqq, line_dash="dash", line_color="#0068C9", annotation_text="QQQ")
        fig.update_layout(coloraxis_showscale=False, margin=dict(t=50, b=10))
        return fig

    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    c1.plotly_chart(quick_bar(stocks_report, 'Volatility', 'Annual Risk (Sigma)', spy_val['Volatility'], qqq_val['Volatility']), use_container_width=True)
    c2.plotly_chart(quick_bar(stocks_report, 'Beta', 'Systematic Risk (Beta)', 1.0, qqq_val['Beta']), use_container_width=True)
    c3.plotly_chart(quick_bar(stocks_report, 'Alpha', "Jensen's Alpha", 0.0, qqq_val['Alpha']), use_container_width=True)
    c4.plotly_chart(quick_bar(stocks_report, 'Sharpe Ratio', 'Sharpe Ratio', spy_val['Sharpe Ratio'], qqq_val['Sharpe Ratio']), use_container_width=True)

    # 4. Dispersion & Correlation
    st.divider()
    st.subheader("Statistical Distributions & Dependencies")
    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        ann_returns_raw = pd.DataFrame({t: all_data[t]['return_pct'] * 252 for t in settings.tickers})
        log_returns = np.sign(ann_returns_raw) * np.log1p(np.abs(ann_returns_raw)) * 100
        fig_box = px.box(log_returns.melt(), x="variable", y="value", points=False, title="<b>Annual Variance (Log-Scaled)</b>", template="plotly_dark", color="variable")
        fig_box.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)
    with col_right:
        corr_matrix = ann_returns_raw.corr()
        fig_corr = px.imshow(corr_matrix.mask(np.triu(np.ones_like(corr_matrix, dtype=bool))), text_auto=".2f", color_continuous_scale='Spectral_r', zmin=-1, zmax=1, template="plotly_dark")
        fig_corr.update_traces(textfont=dict(size=14, family="Arial Black"))
        fig_corr.update_layout(title="<b>Correlation Matrix</b>")
        st.plotly_chart(fig_corr, use_container_width=True)

    # =================================================================
    # PART II: PORTFOLIO SIMULATOR (ACTIVE)
    # =================================================================
    st.header("Section II: Portfolio Strategy Simulator")
    
    st.markdown('<div class="simulator-panel">', unsafe_allow_html=True)
    
    inst_col, weight_col, result_col = st.columns([0.8, 1, 1.8])
    
    with inst_col:
        st.write("### 📖 Guide")
        st.markdown(f"""
        <div class="instruction-text">
        Based on the historical analysis above, use this simulator to check 
        <b>portfolio diversification effects</b>. <br><br>
        1. Adjust sliders to allocate capital.<br>
        2. Ensure total weight is 100%.<br>
        3. Observe how <b>Portfolio Volatility</b> compares to individual stock risks.
        </div>
        """, unsafe_allow_html=True)

    with weight_col:
        st.write("### 🛠️ Weights")
        weights = {ticker: st.slider(f"{ticker}", 0, 100, 100 // len(stocks_only_list)) for ticker in stocks_only_list}
        total_w = sum(weights.values())
        if total_w != 100: 
            st.error(f"Current: {total_w}%")
        else: 
            st.success("Target Met")

    with result_col:
        st.write("### 📈 Live Results")
        returns_only = pd.DataFrame({t: all_data[t]['return_pct'] for t in stocks_only_list})
        w_vec = np.array([weights[t]/100 for t in stocks_only_list])
        p_ret = np.sum(returns_only.mean() * 252 * w_vec)
        p_vol = np.sqrt(np.dot(w_vec.T, np.dot(returns_only.cov() * 252, w_vec)))
        
        met_c1, met_c2, met_c3 = st.columns(3)
        met_c1.metric("Sim. Return", f"{p_ret:.2%}")
        met_c2.metric("Sim. Volatility", f"{p_vol:.2%}")
        # Note: Sharpe will be negative if Sim. Return < 4% (0.04)
        met_c3.metric("Sharpe", f"{(p_ret - 0.04)/p_vol:.2f}" if p_vol != 0 else "0.00")
        
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=stocks_only_list, y=stocks_report['Volatility'], marker_color="#334155"))
        fig_comp.add_hline(y=p_vol, line_dash="dash", line_color="#00ff88", line_width=4, annotation_text="PORTFOLIO LEVEL")
        fig_comp.update_layout(title="<b>Volatility Reduction Proof</b>", template="plotly_dark", height=230, margin=dict(t=40, b=0), showlegend=False)
        st.plotly_chart(fig_comp, use_container_width=True)
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    conn.close()

except Exception as e:
    st.error(f"Application Error: {e}")