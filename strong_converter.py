import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Config ---
DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "lifting_log.csv")

# --- Streamlit UI ---
st.set_page_config(page_title="Strong CSV Converter", layout="wide")
st.title("📥 Strong CSV to Lifting Log Converter")

uploaded_file = st.file_uploader("Upload your Strong export (.csv)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Session ID"] = df["Date"].dt.date.astype(str) + " - " + df["Exercise Name"]
    df.sort_values(by=["Session ID", "Set Order"], inplace=True)

    # --- Warmup logic (fixed) ---
    def determine_set_type(group):
        max_weight = group["Weight"].max()
        max_weight_idx = group[group["Weight"] == max_weight].index[0]

        # Always mark sets with <=2 reps as warmups
        force_warmup = group["Reps"] <= 2

        # Additional warmups: lighter sets before top set
        lighter_before_top = (group["Weight"] < max_weight) & (group.index < max_weight_idx)

        is_warmup = force_warmup | lighter_before_top
        return is_warmup.map(lambda x: "Warmup" if x else "Working")

    df["Set Type"] = df.groupby("Session ID").apply(determine_set_type).reset_index(level=0, drop=True)

    # --- Auto-fill Workout Title from 'Workout Name' ---
    df["Workout Title"] = df["Workout Name"].fillna("")

    # --- Reformat for export ---
    export_df = df.rename(columns={
        "Exercise Name": "Exercise",
        "RPE": "RPE",
        "Notes": "Notes"
    })

    final_df = export_df[[
        "Date", "Workout Title", "Exercise", "Set Order", "Set Type",
        "Weight", "Reps", "RPE", "Notes"
    ]]

    # --- Display + download ---
    st.success("✅ File converted successfully!")
    st.dataframe(final_df)

    csv_out = final_df.to_csv(index=False).encode("utf-8")
    filename = f"converted_lifting_log_{datetime.now().date()}.csv"

    st.download_button(
        label="📥 Download Converted Log",
        data=csv_out,
        file_name=filename,
        mime="text/csv"
    )

    # --- Append to lifting_log.csv with smart merge ---
    st.markdown("---")
    if st.checkbox("📎 Append to existing lifting_log.csv (smart merge)"):
        os.makedirs(DATA_DIR, exist_ok=True)

        if os.path.exists(LOG_FILE):
            existing_log = pd.read_csv(LOG_FILE)
            combined = pd.concat([existing_log, final_df], ignore_index=True)

            # Drop duplicates based on key workout identifiers
            combined.drop_duplicates(
                subset=["Date", "Exercise", "Set Order", "Weight", "Reps"],
                keep="first",
                inplace=True
            )
        else:
            combined = final_df

        combined.to_csv(LOG_FILE, index=False)
        st.success(f"✅ Cleanly merged and saved to {LOG_FILE}")

else:
    st.info("Upload a Strong CSV file to begin.")
