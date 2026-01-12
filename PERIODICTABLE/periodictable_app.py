"""Simple Streamlit app for exploring the periodic table using `periodictable`.

Run with:
  source venv314/bin/activate
  streamlit run PERIODICTABLE/periodictable_app.py

Features:
 - Search by name or symbol (case-insensitive)
 - Browse full elements table and filter by atomic number range
 - Select an element to view details and download CSV of the table
"""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import streamlit as st

try:
    import periodictable as pt
except Exception:
    pt = None


st.set_page_config(page_title="Periodic Table Explorer", layout="wide")
st.title("Periodic Table Explorer")

if pt is None:
    st.error("The 'periodictable' package is not installed in this environment.\nInstall with: pip install periodictable")
    st.stop()


@st.cache_data
def build_elements_df() -> pd.DataFrame:
    rows = []
    for attr in dir(pt):
        # element attributes are single-letter or capitalized symbols like 'H', 'He',
        # but periodictable also exposes other names. We filter down to objects with .number
        try:
            obj = getattr(pt, attr)
        except Exception:
            continue
        if hasattr(obj, "number") and getattr(obj, "number") is not None:
            rows.append(
                {
                    "name": getattr(obj, "name", ""),
                    "symbol": getattr(obj, "symbol", attr),
                    "number": getattr(obj, "number", None),
                    "mass": getattr(obj, "mass", None),
                    "density": getattr(obj, "density", None),
                    "melting_point": getattr(obj, "melting_point", None),
                    "boiling_point": getattr(obj, "boiling_point", None),
                }
            )
    df = pd.DataFrame(rows)
    # Remove any rows missing an atomic number and deduplicate by atomic number.
    if not df.empty:
        df = df[df["number"].notnull()].copy()
        # Some periodictable objects may expose the number as a float; make it int for deduping
        try:
            df["number"] = df["number"].astype(int)
        except Exception:
            # If conversion fails, keep original values but still attempt dedupe
            pass
        df = df.drop_duplicates(subset=["number"]).sort_values("number").reset_index(drop=True)
    return df


df = build_elements_df()

with st.sidebar:
    st.header("Search / Filters")
    query = st.text_input("Element name or symbol (or leave empty to browse)")
    min_num, max_num = int(df["number"].min()), int(df["number"].max())
    num_range = st.slider("Atomic number range", min_value=min_num, max_value=max_num, value=(min_num, max_num))
    show_only_with_density = st.checkbox("Show only elements with density data", value=False)
    download_all = st.button("Download table CSV")

filtered = df[(df["number"] >= num_range[0]) & (df["number"] <= num_range[1])]
if show_only_with_density:
    filtered = filtered[filtered["density"].notnull()]

if query:
    q = query.strip()
    # lookup strategies
    sel = None
    sel = filtered[filtered["symbol"].str.lower() == q.lower()]
    if sel.empty:
        sel = filtered[filtered["name"].str.lower() == q.lower()]
    if sel.empty:
        # contains
        sel = filtered[filtered["name"].str.lower().str.contains(q.lower()) | filtered["symbol"].str.lower().str.contains(q.lower())]
    st.subheader(f"Search results for '{query}'")
    if sel.empty:
        st.info("No elements match your query.")
    else:
        st.dataframe(sel.set_index("number"))
        # If a single result, show details
        if len(sel) == 1:
            row = sel.iloc[0]
            st.markdown("---")
            st.header(f"{row['name']} ({row['symbol']}) — Details")
            cols = st.columns(2)
            with cols[0]:
                st.metric("Atomic number", int(row["number"]))
                st.write("**Mass**:", row["mass"])
                st.write("**Density**:", row["density"])
            with cols[1]:
                st.write("**Melting point (K)**:", row["melting_point"])
                st.write("**Boiling point (K)**:", row["boiling_point"])

else:
    st.subheader("Elements")
    st.dataframe(filtered.set_index("number"))

if download_all:
    csv = filtered.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="periodic_table_filtered.csv", mime="text/csv")

# Always offer CSV download for current filtered view
buf = io.StringIO()
filtered.to_csv(buf, index=False)
st.download_button("Download current view as CSV", data=buf.getvalue(), file_name="periodic_table_view.csv", mime="text/csv")

st.markdown("\n---\nBuilt with the `periodictable` package.\nYou can install it with `pip install periodictable` if missing.")
