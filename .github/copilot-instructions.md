## Project snapshot

This repository contains two small Streamlit apps and a forecasting script:

- `myfirstcode/streamlit_app.py` — Streamlit dashboard that runs the RBC (RY.TO) forecast using `rbc_forecast.py` utilities.
- `myfirstcode/rbc_forecast.py` — Core forecasting logic: downloads data via `yfinance`, normalizes columns, trains `prophet`, evaluates (RMSE/MAPE), and writes CSV/PNG outputs (`rbc_forecast_<TICKER>.csv` / `.png`).
- `PERIODICTABLE/periodictable_app.py` — Small Streamlit explorer built on the `periodictable` package.
- `dashboard/functionality.txt` — short note with intended dashboard behaviour (one-line TODO).
- `myfirstcode/requirements.txt` and `myfirstcode/requirement.txt` — duplicate requirement lists (prefer `requirements.txt`).

Keep examples brief and operate from the repository subfolder `myfirstcode/` when running the apps. Many run instructions in the local README assume that location.

## What to know before editing

- Runtime: code targets Python 3 and uses a venv. README suggests:

  source venv/bin/activate
  pip install -r requirements.txt

- Primary external integrations:
  - yfinance for historical OHLC data
  - prophet (PyPI `prophet`) for forecasting; optional `cmdstanpy` for CmdStan installation
  - streamlit + plotly for dashboards and interactive plots
  - periodictable for the periodic table app

- Data I/O:
  - Forecast outputs are written to CSV/PNG in the same folder as `rbc_forecast.py` (e.g., `rbc_forecast_RY_TO.csv`).
  - Example input: no bundled datasets — `fetch_data` pulls from the web via `yfinance`.

## Codebase patterns and conventions (useful for AI edits)

- Fetch/normalize: `fetch_data` in `rbc_forecast.py` handles MultiIndex columns from `yfinance`. If adding alternate data sources, keep the output shape: DataFrame with columns `['ds', 'y']` and no NaNs.

- Train/eval split: `train_and_forecast(df, forecast_days)` uses `test_days = min(forecast_days, 90)` and slices the last `test_days` for evaluation. When changing evaluation behavior, update both `streamlit_app.py` and `rbc_forecast.py` consistently.

- Caching: Streamlit apps use `@st.cache_data(...)` for the full-model forecast and element table builder — preserve or update cache keys when changing input arguments.

- PNG export: `streamlit_app.py` attempts `fig.write_image(...)` and falls back with a warning if `kaleido` isn't installed. If adding image exports, follow the same try/except pattern to avoid breaking the UI.

- Signal logic: `streamlit_app.py` implements three signal methods (`percent_threshold`, `ma_crossover`, `composite`) — these functions expect specific column names (`ds`, `y`, `pred`) and types (`date` as `datetime.date` for predictions). Keep that contract when refactoring.

## Developer workflows (what to run)

- Create and activate a venv (macOS zsh):

  python3 -m venv venv
  source venv/bin/activate

- Install dependencies (from the repo or the `myfirstcode/` folder where `requirements.txt` lives):

  pip install -r myfirstcode/requirements.txt

- Run the forecast script (execute from the repo root or `myfirstcode/`):

  python myfirstcode/rbc_forecast.py --ticker RY.TO --start 2010-01-01 --days 90

- Run Streamlit apps:

  streamlit run myfirstcode/streamlit_app.py
  streamlit run PERIODICTABLE/periodictable_app.py

Notes: the README inside `myfirstcode/` shows similar commands; use the exact paths above to avoid confusion.

## Project-specific gotchas and actionables for AI agents

- requirements files: there are two similar files (`requirement.txt` and `requirements.txt`). Use `requirements.txt` as canonical and update it when adding packages. Keep an eye on `prophet` vs historical `fbprophet` naming.

- Empty placeholder: `myfirstcode/myfirstaicode.py` exists but is empty — if asked to add helper utilities, confirm intended purpose first (it's safe to add a small CLI wrapper or tests here).

- Minimal testing: this repo currently has no tests. If adding tests, prefer small unit tests around `fetch_data`, `train_and_forecast`, and `evaluate`; these are pure functions that can be exercised with a sample DataFrame.

- Safe edits to Streamlit code: avoid blocking UI during long downloads/fits — prefer using `@st.cache_data` for cached results or offload heavy work to background threads/processes. When changing function signatures that are cached, update the cache key or TTL.

## Examples of prompts that produce good edits

- "Update `rbc_forecast.py` to accept a `--output-dir` flag and write CSV/PNG there. Keep current default filenames but make them relative to `--output-dir`. Update README and CLI help accordingly."

- "Add a unit test that constructs a small synthetic `ds`/`y` DataFrame, runs `train_and_forecast(..., forecast_days=10)` and asserts `evaluate` returns numeric RMSE. Place tests under `tests/test_forecast.py`."

- "Make Streamlit PNG export optional: add a config flag `EXPORT_PNG` in `streamlit_app.py` that disables `fig.write_image` if False. Ensure fallback message is unchanged."

## Relevant files to inspect when making changes

- `myfirstcode/rbc_forecast.py` — data normalization, training, evaluation, plotting.
- `myfirstcode/streamlit_app.py` — integration, UI controls, caching, signal logic.
- `PERIODICTABLE/periodictable_app.py` — a reference Streamlit pattern (caching + CSV download).
- `myfirstcode/requirements.txt` and `myfirstcode/requirement.txt` — dependency lists; keep `requirements.txt` authoritative.
- `dashboard/functionality.txt` — feature notes; check before implementing new UI features.

If anything is unclear or you want me to include explicit tests, CI config, or a sample synthetic dataset, tell me which piece to prioritize and I will update this file.
