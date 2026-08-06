import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="AI Stock Trading", layout="wide")

# Money & Portfolio
if "cash" not in st.session_state:
    st.session_state.cash = 10000000.0
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {} # {ticker: {"qty": 10, "avg_price": 1325}}

st.sidebar.title("⚙️ Settings")
ticker = st.sidebar.selectbox("Select Stock", ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "AAPL", "GOOGL"])
qty = st.sidebar.number_input("Quantity", 1, 100, 10)
st.sidebar.metric("Available Cash", f"Rs.{st.session_state.cash:,.2f}")
st.sidebar.metric("Stocks Owned", len(st.session_state.portfolio))

# Logo + Title
col1, col2 = st.columns([1, 5])
with col1:
    st.image(st.image("logo.png", width=80))
with col2:
    st.title("TradeGenie")
    st.caption("NSE + NASDAQ Stocks | AI Powered Paper Trading")

# DISCLAIMER ADDED HERE
st.warning("⚠️ **Disclaimer**: This is a PAPER TRADING app for educational purposes only. AI predictions are not financial advice. Do not use this for real money trading. Market data may be delayed.", icon="🚨")

tab1, tab2 = st.tabs(["📈 Predictor", "💼 My Portfolio"])

@st.cache_data
def get_data(tick):
    data = yf.download(tick, period="6mo", auto_adjust=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data.dropna()

def predict(data):
    df = data.reset_index()
    df["day"] = np.arange(len(df))
    X, y = df[["day"]], df["Close"]
    model = LinearRegression().fit(X, y)
    current = float(y.iloc[-1])
    pred = float(model.predict([[len(df)]])[0])
    return current, pred

with tab1:
    data = get_data(ticker)

    if not data.empty:
        current, predicted = predict(data)
        change = ((predicted - current) / current) * 100
        signal = "🟢 Trade UP" if predicted > current else "🔴 Trade DOWN"

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Price", f"Rs.{current:,.2f}")
        c2.metric("Predicted Price", f"Rs.{predicted:,.2f}", f"{change:.2f}%")
        c3.metric("AI Signal", signal)

        fig = go.Figure(go.Candlestick(x=data.index,
                        open=data["Open"], high=data["High"],
                        low=data["Low"], close=data["Close"]))
        fig.update_layout(height=400, xaxis_rangeslider_visible=False, title=f"{ticker} Chart")
        st.plotly_chart(fig, use_container_width=True)

        colb1, colb2 = st.columns(2)
        with colb1:
            if st.button("🟢 Buy Stock", type="primary", use_container_width=True):
                cost = current * qty
                if cost <= st.session_state.cash:
                    st.session_state.cash -= cost

                    if ticker in st.session_state.portfolio:
                        old_qty = st.session_state.portfolio[ticker]["qty"]
                        old_avg = st.session_state.portfolio[ticker]["avg_price"]
                        new_qty = old_qty + qty
                        new_avg = ((old_qty * old_avg) + (qty * current)) / new_qty
                        st.session_state.portfolio[ticker] = {"qty": new_qty, "avg_price": new_avg}
                    else:
                        st.session_state.portfolio[ticker] = {"qty": qty, "avg_price": current}

                    st.success(f"Bought {qty} shares of {ticker} at Rs.{current:,.2f}")
                    st.rerun()
                else:
                    st.error("Not enough cash")

        with colb2:
            if st.button("🔴 Sell Stock", use_container_width=True):
                if ticker in st.session_state.portfolio and st.session_state.portfolio[ticker]["qty"] >= qty:
                    st.session_state.portfolio[ticker]["qty"] -= qty
                    st.session_state.cash += current * qty
                    if st.session_state.portfolio[ticker]["qty"] == 0:
                        del st.session_state.portfolio[ticker]
                    st.success(f"Sold {qty} shares of {ticker} at Rs.{current:,.2f}")
                    st.rerun()
                else:
                    st.error("Not enough shares to sell")
    else:
        st.error("Data not found")

with tab2:
    st.header("💼 My Portfolio")

    if not st.session_state.portfolio:
        st.info("No stocks owned yet. Go to Predictor tab to buy.")
    else:
        portfolio_data = []
        total_value = 0
        total_invested = 0

        for stock, details in st.session_state.portfolio.items():
            q = details["qty"]
            avg_price = details["avg_price"]
            stock_data = get_data(stock)
            if not stock_data.empty:
                curr_price = float(stock_data["Close"].iloc[-1])
                invested = avg_price * q
                value = curr_price * q
                pnl = value - invested
                pnl_pct = (pnl / invested) * 100 if invested > 0 else 0

                total_value += value
                total_invested += invested

                portfolio_data.append({
                    "Stock": stock,
                    "Quantity": q,
                    "Avg Buy Price": f"Rs.{avg_price:,.2f}",
                    "Current Price": f"Rs.{curr_price:,.2f}",
                    "P/L": f"Rs.{pnl:,.2f}",
                    "P/L %": f"{pnl_pct:.2f}%",
                    "Total Value": f"Rs.{value:,.2f}"
                })

        if portfolio_data:
            df_port = pd.DataFrame(portfolio_data)
            st.dataframe(df_port, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.metric("Total Portfolio Value", f"Rs.{total_value:,.2f}")
            col2.metric("Total Invested", f"Rs.{total_invested:,.2f}")

    st.divider()
    if st.button("🔄 Reset Portfolio & Cash"):
        st.session_state.cash = 10000000.0
        st.session_state.portfolio = {}
        st.success("Reset Complete")
        st.rerun()

# FOOTER DISCLAIMER
st.divider()
st.caption("Built with ❤️ using Streamlit + yFinance + AI. This app does not connect to any real broker. All trades are simulated.")
