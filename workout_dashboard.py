import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go


# --- File paths ---
DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "lifting_log.csv")

# --- Load and preprocess data ---
def load_lifting_data():
    df = pd.read_csv(LOG_FILE)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

def filter_working_sets(df):
    return df[df["Set Type"].str.lower() == "working"].copy()

def compute_estimated_1rm(df):
    df["Estimated 1RM"] = df["Weight"] * (1 + df["Reps"] / 30)
    return df

def compute_session_average_load(df):
#The math for this function doesnt really work the best. I may rework it to be (reps+rir) * weight / sets or just (reps+rir) * weight for the top set only
#The goal of this function to calculate if you are progressing by factoring both weight and reps
    df["Volume"] = df["Weight"] * df["Reps"]
    grouped = df.groupby(["Exercise", df["Date"].dt.date])
    avg_load_df = grouped.agg(
        TotalVolume=("Volume", "sum"),
        NumSets=("Volume", "count")
    ).reset_index()
    avg_load_df["Session Average Load"] = avg_load_df["TotalVolume"] / avg_load_df["NumSets"]
    avg_load_df.rename(columns={"Date": "Session Date"}, inplace=True)
    return avg_load_df

# --- Streamlit App ---
st.set_page_config(page_title="Lifting Dashboard", layout="wide")
st.title("🏋️ Lifting Progress Dashboard")

# Load and process data
if os.path.exists(LOG_FILE):
    df_raw = load_lifting_data()
    df_working = filter_working_sets(df_raw)
    df_working = compute_estimated_1rm(df_working)
    df_working["Volume"] = df_working["Weight"] * df_working["Reps"]
    df_avg = compute_session_average_load(df_working)

    # UI - Chart Controls
    exercise_list = sorted(df_working["Exercise"].unique())
    selected_exercise = st.selectbox("Choose an exercise", exercise_list)

    chart_type = st.selectbox(
        "Select a chart to display",
        ["Max Weight Over Time", "Estimated 1RM Over Time", "Session Average Load"]
    )

    df_filtered = df_working[df_working["Exercise"] == selected_exercise]
    df_avg_filtered = df_avg[df_avg["Exercise"] == selected_exercise]

    # Date range filter
    min_date = df_filtered["Date"].min().date()
    max_date = df_filtered["Date"].max().date()
    date_range = st.date_input("Filter by date", [min_date, max_date])

    if len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df_filtered = df_filtered[(df_filtered["Date"] >= start) & (df_filtered["Date"] <= end)]
        df_avg_filtered = df_avg_filtered[
            (pd.to_datetime(df_avg_filtered["Session Date"]) >= start) &
            (pd.to_datetime(df_avg_filtered["Session Date"]) <= end)
        ]

    # --- Chart rendering with Plotly ---
    if chart_type == "Max Weight Over Time":
        fig = px.line(df_filtered, x="Date", y="Weight", title="Max Weight Over Time", markers=True)

    elif chart_type == "Estimated 1RM Over Time":
        df_sorted = df_filtered.sort_values("Date")
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_sorted["Date"],
            y=df_sorted["Estimated 1RM"],
            mode="lines+markers",
            name="Estimated 1RM"
        ))

        df_sorted["1RM MA"] = df_sorted["Estimated 1RM"].rolling(window=3).mean()
        fig.add_trace(go.Scatter(
            x=df_sorted["Date"],
            y=df_sorted["1RM MA"],
            mode="lines",
            name="3-pt Moving Avg",
            line=dict(dash="dash")
        ))

        fig.update_layout(title="Estimated 1RM Over Time", xaxis_title="Date", yaxis_title="1RM")

    else:  # Session Average Load
        fig = px.line(
            df_avg_filtered,
            x="Session Date",
            y="Session Average Load",
            title="Session Average Load Over Time",
            markers=True
        )

    st.plotly_chart(fig, use_container_width=True)

    # --- Summary stats ---
    st.markdown("### 📊 Summary for Selected Exercise")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Sessions Logged", df_avg_filtered.shape[0])
        st.metric("Max Weight", f"{df_filtered['Weight'].max():.1f}")

    with col2:
        st.metric("Max Est. 1RM", f"{df_filtered['Estimated 1RM'].max():.1f}")
        st.metric("Avg Reps/Set", f"{df_filtered['Reps'].mean():.1f}")

    with col3:
        st.metric("Avg Session Load", f"{df_avg_filtered['Session Average Load'].mean():.1f}")
        st.metric("Total Sets", df_filtered.shape[0])

    # --- Detailed table ---
    st.markdown("---")
    st.subheader("📋 Set-Level Data")
    st.dataframe(df_filtered[[ 
        "Date", "Workout Title", "Exercise", "Set Type", "Weight", "Reps", "RIR", "Estimated 1RM", "Volume"
    ]].sort_values("Date", ascending=False), use_container_width=True)

else:
    st.warning("No log file found. Please log a workout first.")
