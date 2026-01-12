# RBC (RY.TO) forecasting

This small project downloads historical close prices for Royal Bank of Canada (ticker `RY.TO`) and forecasts future prices using Prophet.

Quick start

1. Create and activate a venv (macOS zsh):

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install requirements:

```bash
pip install -r "/Users/tanujkhator/untitled folder/python_code/requirement.txt"
```

3. (Optional) If `cmdstanpy` is installed, you may need to install CmdStan once:

```bash
python -c "import cmdstanpy; cmdstanpy.install_cmdstan()"
```

4. Run the forecast script:

```bash
python "/Users/tanujkhator/untitled folder/python_code/rbc_forecast.py" --ticker RY.TO --start 2010-01-01 --days 90
```

Outputs

- `rbc_forecast_RY_TO.csv` — forecast table (ds, yhat, yhat_lower, yhat_upper)
- `rbc_forecast_RY_TO.png` — plot with historicals and forecast

If you want a Jupyter notebook or automated tests, tell me and I will add them.
