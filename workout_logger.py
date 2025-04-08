import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ---------- Config ----------
DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "lifting_log.csv")
EXERCISE_FILE = os.path.join(DATA_DIR, "exercises.csv")
TEMPLATE_DIR = os.path.join(DATA_DIR, "templates")

# ---------- Ensure folders/files exist ------
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(EXERCISE_FILE):
    pd.DataFrame(columns=["Exercise Name"]).to_csv(EXERCISE_FILE, index=False)

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=[
        "Date", "Workout Title", "Exercise", "Set Order", "Set Type",
        "Weight", "Reps", "RPE", "Notes"
    ]).to_csv(LOG_FILE, index=False)

# ---------- Load exercises ----------
def load_exercises():
    return pd.read_csv(EXERCISE_FILE)["Exercise Name"].tolist()

def save_exercise(new_exercise):
    current = pd.read_csv(EXERCISE_FILE)
    if new_exercise not in current["Exercise Name"].values:
        updated = pd.concat([current, pd.DataFrame([{"Exercise Name": new_exercise}])], ignore_index=True)
        updated.to_csv(EXERCISE_FILE, index=False)

# ---------- Template loader ----------
def load_template(name):
    path = os.path.join(TEMPLATE_DIR, name + ".json")
    with open(path, "r") as f:
        return json.load(f)

template_names = [f.replace(".json", "") for f in os.listdir(TEMPLATE_DIR) if f.endswith(".json")]

# ---------- UI ----------
st.title("🏋️ Workout Logger")

col1, col2 = st.columns([2, 1])
with col1:
    workout_title = st.text_input("Workout Title", value="")
with col2:
    session_date = st.date_input("Date", value=date.today())

selected_template = st.selectbox("📄 Load a Template", ["None"] + template_names)
if selected_template != "None":
    preset_rows = load_template(selected_template)
    session_df = pd.DataFrame(preset_rows)
    # Remove Set Order from editable view — it's assigned at save time
    if "Set Order" in session_df.columns:
        session_df.drop(columns=["Set Order"], inplace=True)

else:
    session_df = pd.DataFrame(columns=[
        "Exercise", "Set Type", "Weight", "Reps", "RPE", "Notes"
    ])

# ---------- Add set manually ----------
st.markdown("### 📝 Edit Session Log")
edited_df = st.data_editor(session_df, num_rows="dynamic", use_container_width=True)

# ---------- Add new exercise ----------
with st.expander("➕ Add New Exercise"):
    new_ex = st.text_input("Exercise Name")
    if st.button("Add Exercise") and new_ex:
        save_exercise(new_ex)
        st.success(f"Added '{new_ex}' to exercise list.")

# ---------- Save workout ----------
if st.button("💾 Save Session"):
    if edited_df.empty or not workout_title.strip():
        st.warning("Please enter a workout title and at least one set.")
    else:
        # Auto-assign Set Order
        df = edited_df.copy()
        df["Set Order"] = None

        for exercise in df["Exercise"].dropna().unique():
            mask = df["Exercise"] == exercise
            df.loc[mask, "Set Order"] = list(range(1, mask.sum() + 1))

        # Add metadata
        df["Date"] = pd.to_datetime(session_date)
        df["Workout Title"] = workout_title

        # Save to file
        log_df = pd.read_csv(LOG_FILE)
        updated_log = pd.concat([log_df, df], ignore_index=True)
        updated_log.to_csv(LOG_FILE, index=False)

        st.success("Workout saved to log!")
        st.experimental_rerun()

