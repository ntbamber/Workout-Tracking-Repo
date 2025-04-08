import streamlit as st
import pandas as pd
import os
import json

# ---------- Config ----------
DATA_DIR = "data"
TEMPLATE_DIR = os.path.join(DATA_DIR, "templates")
EXERCISE_FILE = os.path.join(DATA_DIR, "exercises.csv")

# ---------- Ensure folders/files exist ----------
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(EXERCISE_FILE):
    pd.DataFrame(columns=["Exercise Name"]).to_csv(EXERCISE_FILE, index=False)

def load_exercises():
    return pd.read_csv(EXERCISE_FILE)["Exercise Name"].tolist()

def save_exercise(new_ex):
    current = pd.read_csv(EXERCISE_FILE)
    if new_ex not in current["Exercise Name"].values:
        updated = pd.concat([current, pd.DataFrame([{"Exercise Name": new_ex}])], ignore_index=True)
        updated.to_csv(EXERCISE_FILE, index=False)

def save_template(name, data):
    path = os.path.join(TEMPLATE_DIR, name + ".json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_template(name):
    path = os.path.join(TEMPLATE_DIR, name + ".json")
    with open(path, "r") as f:
        return json.load(f)

# ---------- UI ----------
st.title("🧱 Template Creator")

template_names = [f.replace(".json", "") for f in os.listdir(TEMPLATE_DIR) if f.endswith(".json")]
template_mode = st.radio("Create or Edit?", ["Create New", "Edit Existing"])

if template_mode == "Create New":
    template_name = st.text_input("🆕 New Template Name")
else:
    template_name = st.selectbox("✏️ Edit Template", template_names)
    if template_name:
        preset_data = load_template(template_name)
    else:
        preset_data = []

# ---------- Build/Edit Table ----------
st.markdown("### 🏗️ Build Your Template")
exercise_list = load_exercises()

default_df = pd.DataFrame(preset_data if template_mode == "Edit Existing" and template_name else [], columns=[
    "Exercise", "Set Type", "Weight", "Reps", "RPE", "Notes"
])

edited_df = st.data_editor(default_df, num_rows="dynamic", use_container_width=True)

# ---------- Add new exercise ----------
with st.expander("➕ Add New Exercise"):
    new_ex = st.text_input("Exercise Name")
    if st.button("Add Exercise") and new_ex:
        save_exercise(new_ex)
        st.success(f"Added '{new_ex}' to exercise list.")

# ---------- Save template ----------
if st.button("💾 Save Template"):
    if not template_name.strip():
        st.warning("Please enter a template name.")
    elif edited_df.empty:
        st.warning("Template cannot be empty.")
    else:
        # Auto-set Set Order by Exercise
        df = edited_df.copy()
        df["Set Order"] = None

        for exercise in df["Exercise"].dropna().unique():
            mask = df["Exercise"] == exercise
            df.loc[mask, "Set Order"] = list(range(1, mask.sum() + 1))

        # Save as JSON
        save_template(template_name.strip(), df.to_dict(orient="records"))
        st.success(f"Template '{template_name}' saved!")

