import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from streamlit.components.v1 import html

from matplotlib.ticker import StrMethodFormatter
import random
from adapted import runsim

# --- PAGE CONFIG ---
st.set_page_config(page_title="Portfolio Forecast App", layout="wide")

# --- APP TITLE ---
#st.title("Portfolio Forecasting Dashboard")

# --- LAYOUT ---
col_tl, col_tr = st.columns([1, 2])
col_bl, col_br = st.columns([1, 2])

# --- TOP LEFT: Current Price ---
with col_tl:
    ticker_symbol = st.session_state.get("ticker", "AAPL")
    st.header(ticker_symbol)
    #st.caption(yf.Ticker(ticker_symbol).info["shortName"])
    try:
        financialData = yf.Ticker(ticker_symbol).history(period="10y")
    except:
        st.error("Could not fetch data. Please check the ticker symbol.")
        financialData  = yf.Ticker("aapl").history(period="10y")
    
    dailyReturns = financialData['Close'].pct_change().dropna()
    marketData = yf.Ticker('^GSPC').history(period="20y")
    marketReturns = marketData['Close'].pct_change().dropna()
    beta = dailyReturns.cov(marketReturns) / marketReturns.var()
    sharpeRatio = (dailyReturns.mean() / dailyReturns.std()) * (252 ** 0.5)
    maxDrawdown = (financialData['Close'] / financialData['Close'].cummax() - 1).min()

    try:
        beta = round(beta, 2)
        sharpeRatio = round(sharpeRatio, 2)
        maxDrawdown = round(maxDrawdown, 2)
    except:
        pass
    
    
    c1, c2, c3 = st.columns(3)
    c1.metric(label="Beta", value=beta)
    c2.metric(label="Sharpe Ratio", value=sharpeRatio)
    c3.metric(label="Max Drawdown", value=maxDrawdown)



    try:
        data = yf.Ticker(ticker_symbol)
        hist = data.history(period="1y")

        current_price = hist["Close"].iloc[-1]
        day_change = (current_price - hist["Close"].iloc[-2]) / hist["Close"].iloc[-2] * 100
        month_change = (current_price - hist["Close"].iloc[-21]) / hist["Close"].iloc[-21] * 100
        year_change = (current_price - hist["Close"].iloc[0]) / hist["Close"].iloc[0] * 100

        def format_change(change):
            arrow = "▲" if change >= 0 else "▼"
            color = "green" if change >= 0 else "red"
            return f"<span style='color:{color}; font-size:20px;'>{arrow} {change:.2f}%</span>"

        # Display metric with larger value text
        st.markdown(f"<h2 style='font-size:34px;'>${current_price:.2f}</h2>", unsafe_allow_html=True)

        # Display changes with larger font size
        st.markdown(
            f"""
            <div style="font-size:20px;">
                <b>1D:</b> {format_change(day_change)} &nbsp;&nbsp;
                <b>30D:</b> {format_change(month_change)} &nbsp;&nbsp;
                <b>1Y:</b> {format_change(year_change)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        #c1, c2 = st.columns(2)
        #c1.metric(label="30D Change", value=f"{month_change:.2f}%")
        #c2.metric(label="1Y Change", value=f"{year_change:.2f}%")

    except Exception as e:
        st.error("Could not fetch data. Please check the ticker symbol.")

# --- TOP RIGHT: TradingView Chart ---
with col_tr:


    def yahoo_to_tradingview(ticker: str) -> str:
        return ticker.split('.')[0].upper()

    ticker_symbol1 = yahoo_to_tradingview(ticker_symbol)




    st.subheader("Live Chart")
    tradingview_html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
          "width": "100%",
          "height": 500,
          "symbol": "{ticker_symbol1}",
          "interval": "D",
          "timezone": "Etc/UTC",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tradingview_chart"
        }});
      </script>
    </div>
    """
    html(tradingview_html, height=550)

# --- BOTTOM LEFT: Input Controls ---
with col_bl:
    st.subheader("Simulation Settings")
    
    ticker_input = st.text_input("Ticker Symbol", value=ticker_symbol, key="ticker")
    if ticker_input == "":
        ticker_input = ticker_symbol

    initial_investment = st.number_input("Initial Investment ($)", value=10000)
    monthly_investment = st.number_input("Monthly Investment ($)", value=100)
    years = st.slider("Time Horizon (years)", 1, 70, 10)
    n_simulations = st.slider("Number of Simulations", 100, 100000, 5000, step=500)
 
    #leverage = st.slider("Leverage (×)", 1.0, 5.0, 1.0, 0.1)

    st.markdown("---")

    #st.subheader("Return Parameters")

    # Fetch up to 70 years of data
    try:
        use_custom = st.checkbox("Override with custom values")
        if not use_custom:
            df = yf.download(ticker_input, period="max", progress=False)
            df = df.tail(70 * 252)  # cap at ~70 years of daily data (~17,640 trading days)
            df["Return"] = df["Close"].pct_change()

            # Compute annualized mean & volatility
            mean_daily_return = df["Return"].mean()
            std_daily_return = df["Return"].std()
            annual_return = mean_daily_return * 252
            annual_volatility = std_daily_return * np.sqrt(252)

            # Calculate date range and years of data
            start_date = df.index.min().date()
            end_date = df.index.max().date()
            years_available = round((end_date - start_date).days / 365.25, 1)

            st.info(
                f"**Historical ({years_available}y, {start_date} → {end_date}):** "
                f"Annual Return ≈ {annual_return*100:.2f}%, "
                f"Volatility ≈ {annual_volatility*100:.2f}%"
            )
        else:
            

            df = yf.download(ticker_input, period="max", progress=False)
            df = df.tail(70 * 252)  # cap at ~70 years of daily data (~17,640 trading days)
            df["Return"] = df["Close"].pct_change()
            mean_daily_return = df["Return"].mean()
            std_daily_return = df["Return"].std()

            #annual_return = mean_daily_return * 252
            #annual_volatility = std_daily_return * np.sqrt(252)

            if "annual_return" not in st.session_state:
                st.session_state.annual_return = 0.0
            if "annual_volatility" not in st.session_state:
                st.session_state.annual_volatility = 0.0

            st.session_state.annual_return = st.number_input(
                "Enter custom annual return", value=st.session_state.annual_return
            )
            st.session_state.annual_volatility = st.number_input(
                "Enter custom volatility", value=st.session_state.annual_volatility
            )

            annual_return = st.session_state.annual_return
            annual_volatility = st.session_state.annual_volatility
            
            start_date = df.index.min().date()
            end_date = df.index.max().date()
            years_available = round((end_date - start_date).days / 365.25, 1)

            st.info(
                f"**Historical ({years_available}y, {start_date} → {end_date}):** "
                f"Annual Return ≈ {annual_return*100:.2f}%, "
                f"Volatility ≈ {annual_volatility*100:.2f}%"
            )
        
        

        if use_custom:
            #custom_return = st.number_input("Expected Annual Return (%)", value=annual_return * 100, step=0.1) / 100
            #custom_vol = st.number_input("Expected Annual Volatility (%)", value=annual_volatility * 100, step=0.1) / 100
            pass
        else:
            pass
            #custom_return = annual_return
            #custom_vol = annual_volatility

        run_simulation = st.button("Run Forecast")

    except Exception as e:
        st.error(f"Could not fetch long-term data: {e}")
        run_simulation = False

# --- BOTTOM RIGHT: Forecast Charts ---
with col_br:
    st.subheader("Monte Carlo Forecast")


    if run_simulation:
        try:
            def plot_fan_chart(result, title=None, savepath=None, show=True):

                x = result['time_years']
                p5 = result['percentiles']['p5']
                p25 = result['percentiles']['p25']
                p50 = result['percentiles']['p50']
                p75 = result['percentiles']['p75']
                p95 = result['percentiles']['p95']
                mean = result['mean']

                fig = plt.figure(figsize=(11,6))

                # 5-95 band
                plt.fill_between(x, p5, p95, alpha=0.18, label='5-95 percentile band')
                # 25-75 band
                plt.fill_between(x, p25, p75, alpha=0.32, label='25-75 percentile band')

                # median and mean
                plt.plot(x, p50, label='Median (50th)', linewidth=1.8)
                plt.plot(x, mean, linestyle='--', label='Mean', linewidth=1.6)

                plt.xlabel('Years')
                plt.ylabel('Portfolio value')
                if title:
                    plt.title(title)
                plt.grid(alpha=0.3)
                plt.legend()

                # currency formatting on y-axis
                ax = plt.gca()
                ax.yaxis.set_major_formatter(StrMethodFormatter('${x:,.0f}'))

                plt.tight_layout()
                st.pyplot(fig)


            result, title = runsim(n_simulations=n_simulations, years=years, annual_volatility=annual_volatility, annual_return=annual_return, monthly_investment=monthly_investment, initial_investment=initial_investment)
            
            plot_fan_chart(result, title=title, savepath=None, show=True)
            final = result['final_stats']
            st.success(f"  Median (50th)  : ${final['median']:,.2f}")
        except Exception as e:
            st.error(f"Simulation failed: {e}")


    