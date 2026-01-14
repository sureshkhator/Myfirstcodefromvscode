# RBC (RY.TO) forecasting

This small project downloads historical close prices for Royal Bank of Canada (ticker `RY.TO`) and forecasts future prices using Prophet.

Quick start

1. Create and activate a venv (macOS zsh):

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install requirements (from this repository root):

```bash
pip install -r requirements.txt
```

3. (Optional) If `cmdstanpy` is installed, you may need to install CmdStan once:

```bash
python -c "import cmdstanpy; cmdstanpy.install_cmdstan()"
```

4. Run the forecast script (from repository root):

```bash
python rbc_forecast.py --ticker RY.TO --start 2010-01-01 --days 90
```

5. Run the Streamlit apps:

```bash
# Forecast dashboard
streamlit run streamlit_app.py

# Periodic-table explorer (in the PERIODICTABLE folder)
streamlit run PERIODICTABLE/periodictable_app.py
```

Outputs

- `rbc_forecast_RY_TO.csv` — forecast table (ds, yhat, yhat_lower, yhat_upper)
- `rbc_forecast_RY_TO.png` — plot with historicals and forecast

If you want a Jupyter notebook or automated tests, tell me and I will add them.
