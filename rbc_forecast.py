#!/usr/bin/env python3
"""Forecast RBC (RY.TO) using Prophet. Creates CSV and PNG outputs.

Usage:
  python rbc_forecast.py --ticker RY.TO --start 2010-01-01 --days 90

This script downloads historical close prices, fits Prophet, creates a forecast,
evaluates against the last `test_days` of history, and saves outputs.
"""
from __future__ import annotations

import argparse
import os
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from prophet import Prophet
from sklearn.metrics import mean_squared_error


def fetch_data(ticker: str = "RY.TO", start: str = "2010-01-01") -> pd.DataFrame:
    df = yf.download(ticker, start=start, progress=False)
    if df.empty:
        return df

    # yfinance sometimes returns MultiIndex columns (e.g. ('Close', 'RY.TO')).
    # Normalize to a simple two-column DataFrame with columns ['ds', 'y']
    if isinstance(df.columns, pd.MultiIndex):
        # Try the common access pattern df['Close'] -> DataFrame or Series
        try:
            close_part = df['Close']
        except Exception:
            # Fall back to searching for a column level that contains 'Close'
            close_part = None
            for col in df.columns:
                if any('Close' == str(x) or 'Close' in str(x) for x in (col if isinstance(col, tuple) else (col,))):
                    close_part = df[col]
                    break

        if close_part is None:
            # As a last resort try 'Adj Close'
            try:
                close_part = df['Adj Close']
            except Exception:
                raise RuntimeError('Could not find Close column in downloaded data')

        # close_part may be a DataFrame (multiple tickers) or a Series
        if isinstance(close_part, pd.DataFrame):
            # take the first column (single ticker expected)
            close_series = close_part.iloc[:, 0]
        else:
            close_series = close_part

        out = close_series.reset_index()
        out.columns = ['ds', 'y']
        out.dropna(inplace=True)
        return out

    # Normal single-level columns
    out = df.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
    out.dropna(inplace=True)
    return out


def train_and_forecast(df: pd.DataFrame, forecast_days: int = 90) -> Tuple[Prophet, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # use up to last 90 days for test (so forecast evaluation is reasonable)
    test_days = min(forecast_days, 90)
    train_df = df[:-test_days].copy()
    test_df = df[-test_days:].copy()

    model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(train_df)

    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)

    return model, forecast, train_df, test_df


def evaluate(forecast: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    pred = forecast[forecast["ds"].isin(test_df["ds"])][["ds", "yhat"]].set_index("ds")
    actual = test_df.set_index("ds")[["y"]]
    joined = actual.join(pred, how="inner")
    if joined.empty:
        return {"rmse": None, "mape": None}
    # compute RMSE manually to avoid compatibility issues across scikit-learn versions
    rmse = float(np.sqrt(np.mean((joined["y"] - joined["yhat"]) ** 2)))
    mape = np.mean(np.abs((joined["y"] - joined["yhat"]) / joined["y"])) * 100
    return {"rmse": float(rmse), "mape": float(mape)}


def plot_and_save(forecast: pd.DataFrame, df: pd.DataFrame, out_csv: str = "rbc_forecast.csv", out_png: str = "rbc_forecast.png") -> None:
    forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(out_csv, index=False)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["ds"], df["y"], label="historical", color="black")
    ax.plot(forecast["ds"], forecast["yhat"], label="forecast", color="tab:blue")
    ax.fill_between(forecast["ds"], forecast["yhat_lower"], forecast["yhat_upper"], color="tab:blue", alpha=0.2)
    ax.legend()
    ax.set_title("RBC (RY.TO) forecast")
    ax.set_xlabel("Date")
    ax.set_ylabel("Close Price")
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Forecast RBC (RY.TO) using Prophet")
    parser.add_argument("--ticker", default="RY.TO", help="Ticker (default: RY.TO)")
    parser.add_argument("--start", default="2010-01-01", help="Start date for historical data")
    parser.add_argument("--days", type=int, default=90, help="Days to forecast")
    args = parser.parse_args()

    df = fetch_data(ticker=args.ticker, start=args.start)
    if df.empty:
        print("No data fetched. Check ticker or internet connection.")
        return

    model, forecast, train_df, test_df = train_and_forecast(df, forecast_days=args.days)
    metrics = evaluate(forecast, test_df)
    if metrics["rmse"] is None:
        print("Could not evaluate: no overlapping test dates with forecast.")
    else:
        print(f"RMSE: {metrics['rmse']:.4f}, MAPE: {metrics['mape']:.2f}%")

    out_csv = f"rbc_forecast_{args.ticker.replace('.', '_')}.csv"
    out_png = f"rbc_forecast_{args.ticker.replace('.', '_')}.png"
    plot_and_save(forecast, df, out_csv=out_csv, out_png=out_png)
    print(f"Saved {out_csv} and {out_png}")


if __name__ == "__main__":
    main()
