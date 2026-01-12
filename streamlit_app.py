"""Streamlit dashboard for RBC forecast.

Run with:
  source venv314/bin/activate
  streamlit run streamlit_app.py
"""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from prophet import Prophet
from rbc_forecast import fetch_data, train_and_forecast, evaluate


def main() -> None:
    st.set_page_config(page_title="RBC Forecast", layout="wide")

    st.title("RBC (RY.TO) Forecast Dashboard")

    with st.sidebar.form("controls"):
        ticker = st.text_input("Ticker", value="RY.TO")
        start = st.date_input("Start date", value=pd.to_datetime("2010-01-01"))
        days = st.number_input("Forecast days", min_value=1, max_value=365, value=90)
        run = st.form_submit_button("Run Forecast")

    if not run:
        return

    with st.spinner("Downloading data and fitting model..."):
        df = fetch_data(ticker=ticker, start=str(start))
        if df.empty:
            st.error("No data returned for ticker. Check symbol or connectivity.")
            return

        model, forecast, train_df, test_df = train_and_forecast(df, forecast_days=days)
        metrics = evaluate(forecast, test_df)

    # Cached helper: compute a full-model forecast for the next N days beyond the
    # last available historical date. We cache on (ticker, start, period) to avoid
    # retraining on each rerun.
    @st.cache_data(ttl=3600)
    def compute_full_forecast(ticker_in: str, start_in: str, period: int):
        df_full = fetch_data(ticker=ticker_in, start=start_in)
        if df_full.empty:
            return None
        m = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
        m.fit(df_full)
        future_full = m.make_future_dataframe(periods=period)
        forecast_full = m.predict(future_full)
        return df_full, forecast_full

    full_res = compute_full_forecast(ticker, str(start), 30)
    next30 = None
    if full_res is not None:
        df_full, forecast_full = full_res
        last_hist = df_full['ds'].max()
        next30 = forecast_full[forecast_full['ds'] > last_hist][['ds', 'yhat', 'yhat_lower', 'yhat_upper']].head(30)

    st.metric("RMSE", f"{metrics['rmse']:.4f}" if metrics["rmse"] is not None else "N/A")
    st.metric("MAPE", f"{metrics['mape']:.2f}%" if metrics["mape"] is not None else "N/A")

    # Plot historical + forecast
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['ds'], y=df['y'], mode='lines', name='Historical'))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast'))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', name='Upper', line=dict(dash='dash'), showlegend=False))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', name='Lower', line=dict(dash='dash'), fill='tonexty', showlegend=False))
    fig.update_layout(title=f"{ticker} Historical and Forecast", xaxis_title='Date', yaxis_title='Price')

    st.plotly_chart(fig, use_container_width=True)

    # Data download
    csv = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(index=False)
    st.download_button("Download forecast CSV", data=csv, file_name=f"forecast_{ticker.replace('.', '_')}.csv", mime='text/csv')

    # Try to export PNG. If Kaleido (plotly image engine) is not available this
    # will raise — we catch exceptions and keep the app running. The CSV
    # download is always available.
    try:
        img_buf = io.BytesIO()
        fig.write_image(img_buf, format='png')
        st.download_button("Download forecast PNG", data=img_buf.getvalue(), file_name=f"forecast_{ticker.replace('.', '_')}.png", mime='image/png')
    except Exception as e:
        st.warning("PNG export unavailable: install 'kaleido' if you need PNG downloads. PNG error: " + str(e))

    # Show next 30-day forecast table and summary (from full-data model)
    if next30 is None or next30.empty:
        st.info("Next-30-day forecast not available.")
    else:
        st.subheader("Next 30 days — predicted close price")
        # show as a nice table
        next30_display = next30.copy()
        next30_display['ds'] = pd.to_datetime(next30_display['ds']).dt.date
        next30_display = next30_display.rename(columns={'ds': 'date', 'yhat': 'pred', 'yhat_lower': 'lower', 'yhat_upper': 'upper'})

        # Buy/sell signal controls
        st.markdown("**Trading signal**")
        signal_method = st.selectbox(
            "Signal method",
            options=["percent_threshold", "ma_crossover", "composite"],
            help="Signal method: percent threshold, moving-average crossover, or composite",
        )
        threshold = st.slider("Signal threshold (% absolute change)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
        # MA crossover params (shown when relevant)
        short_window = st.number_input("Short MA window (days)", min_value=2, max_value=30, value=5)
        long_window = st.number_input("Long MA window (days)", min_value=short_window + 1, max_value=200, value=20)

        # compute last close to compare against
        last_close = df_full["y"].iloc[-1]

        def compute_signal_pct(pred_price: float, last_price: float, thresh_percent: float) -> str:
            pct = (pred_price - last_price) / last_price * 100.0
            if pct >= thresh_percent:
                return "Buy"
            if pct <= -thresh_percent:
                return "Sell"
            return "Hold"

        # MA crossover implementation: build combined series of recent history + predictions
        def compute_ma_signals(df_hist: pd.DataFrame, preds: pd.DataFrame, short_w: int, long_w: int) -> pd.Series:
            # df_hist: columns ['ds','y'], preds: columns ['date','pred'] (date is datetime.date)
            hist = df_hist[["ds", "y"]].copy()
            hist = hist.rename(columns={"ds": "date", "y": "price"})
            hist["date"] = pd.to_datetime(hist["date"]).dt.date
            preds_df = preds.rename(columns={"date": "date", "pred": "price"})[["date", "price"]].copy()
            # combine and sort
            combined = pd.concat([hist, preds_df], ignore_index=True)
            combined = combined.drop_duplicates(subset="date").sort_values("date")
            combined.set_index(pd.to_datetime(combined["date"]), inplace=True)
            price_series = combined["price"]
            # rolling means
            short_ma = price_series.rolling(window=short_w, min_periods=1).mean()
            long_ma = price_series.rolling(window=long_w, min_periods=1).mean()
            ma_df = pd.DataFrame({"price": price_series, "short_ma": short_ma, "long_ma": long_ma})
            # For prediction dates, decide signal based on short vs long MA at that date
            pred_dates = pd.to_datetime(preds["date"])
            signals = []
            for d in pred_dates:
                s = ma_df.loc[d, "short_ma"]
                l = ma_df.loc[d, "long_ma"]
                if s > l:
                    signals.append("Buy")
                elif s < l:
                    signals.append("Sell")
                else:
                    signals.append("Hold")
            return pd.Series(signals, index=preds.index)

        # Composite: majority vote between pct and ma
        def composite_signal(pct_sig: str, ma_sig: str) -> str:
            votes = [pct_sig, ma_sig]
            if votes.count("Buy") > votes.count("Sell"):
                return "Buy"
            if votes.count("Sell") > votes.count("Buy"):
                return "Sell"
            return "Hold"

        # Compute signals based on selected method
        if signal_method == "percent_threshold":
            next30_display["signal"] = next30_display["pred"].apply(lambda p: compute_signal_pct(p, last_close, threshold))
        elif signal_method == "ma_crossover":
            # prepare preds with 'date' and 'pred'
            ma_signals = compute_ma_signals(
                df_full, next30_display.rename(columns={"date": "date", "pred": "pred"}), short_window, long_window
            )
            next30_display["signal"] = ma_signals.values
        else:  # composite
            pct_sigs = next30_display["pred"].apply(lambda p: compute_signal_pct(p, last_close, threshold))
            ma_sigs = compute_ma_signals(
                df_full, next30_display.rename(columns={"date": "date", "pred": "pred"}), short_window, long_window
            )
            next30_display["signal"] = [composite_signal(p, m) for p, m in zip(pct_sigs, ma_sigs)]

        st.dataframe(next30_display.set_index("date"))

        # summary
        st.write("Summary:")
        st.metric("Mean (30 days)", f"{next30_display['pred'].mean():.2f}")
        st.metric("Min (30 days)", f"{next30_display['pred'].min():.2f}")
        st.metric("Max (30 days)", f"{next30_display['pred'].max():.2f}")

        # signal counts
        counts = next30_display["signal"].value_counts().to_dict()
        st.write(f"Signal counts: Buy={counts.get('Buy',0)}, Sell={counts.get('Sell',0)}, Hold={counts.get('Hold',0)}")

        csv30 = next30.to_csv(index=False)
        st.download_button("Download next-30 CSV", data=csv30, file_name=f"next30_{ticker.replace('.', '_')}.csv", mime='text/csv')


if __name__ == "__main__":
    main()
