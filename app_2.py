import os

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Market Investment Awareness", page_icon="📈", layout="wide")

st.markdown("""
<style>
.stApp { background: #11141b; color: #f5f6f8; }
[data-testid="stMetric"] { background: #1b202a; padding: 18px; border-radius: 12px; }
h1, h2, h3, p, label { color: #f5f6f8; }
</style>
""", unsafe_allow_html=True)

st.title("Stock Market Investment Awareness")
st.caption("Survey Dashboard | Built using Python & Streamlit")

DEFAULT_FILES = ["response.csv", "Python (Responses).csv"]

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        path = next((p for p in DEFAULT_FILES if os.path.exists(p)), None)
        if path is None:
            raise FileNotFoundError("No survey CSV found")
        df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df

uploaded = st.sidebar.file_uploader("Upload your survey CSV (optional)", type=["csv"])
try:
    original_df = load_data(uploaded)
except Exception:
    st.error("Survey CSV not found. Place 'response.csv' next to this file, or upload it using the sidebar.")
    st.stop()

if original_df.empty:
    st.warning("The uploaded CSV has no rows.")
    st.stop()

st.sidebar.success(f"{len(original_df)} responses loaded")

age_candidates = [c for c in original_df.columns if "age" in c.lower()]
age_col = age_candidates[0] if age_candidates else None

# Interactive age filter
df = original_df.copy()
if age_col:
    age_options = sorted(df[age_col].dropna().astype(str).unique().tolist())
    selected_ages = st.sidebar.multiselect(
        "Filter by age group",
        options=age_options,
        default=age_options,
        help="Choose one or more age groups to update all dashboard charts and metrics."
    )
    df = df[df[age_col].astype(str).isin(selected_ages)]
    st.sidebar.caption(f"{len(df)} of {len(original_df)} respondents shown")
else:
    st.sidebar.info("No age column was detected, so age filtering is unavailable.")

if df.empty:
    st.warning("No respondents match the selected age group(s). Select at least one age group in the sidebar.")
    st.stop()

exclude = ["Timestamp"]
questions = [c for c in df.columns if c not in exclude and c != age_col]
if not questions:
    st.error("No survey question columns were found in the CSV.")
    st.stop()

n = len(df)
clean = df[questions].astype("string").apply(lambda col: col.str.strip())
yes_total = int(clean.eq("Yes").sum().sum())
total_answers = int(clean.notna().sum().sum())
awareness_pct = (yes_total / total_answers * 100) if total_answers else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Filtered Respondents", f"{n}")
k2.metric("Survey Questions", f"{len(questions)}")
k3.metric("Yes Responses", f"{yes_total}")
k4.metric("Overall Yes Rate", f"{awareness_pct:.1f}%")

left, right = st.columns([1.35, 1])
with left:
    st.subheader("Responses to Awareness Questions")
    first_questions = questions[:min(6, len(questions))]
    response_categories = ["Yes", "No", "Not sure"]
    rows = []
    for i, q in enumerate(first_questions):
        for response in response_categories:
            rows.append({"Question": f"Awareness Q{i+1}",
                         "Response": response, "Respondents": int(clean[q].eq(response).sum())})
    chart_df = pd.DataFrame(rows)
    fig = px.line(chart_df, x="Question", y="Respondents", color="Response", markers=True,
                  color_discrete_map={"Yes":"#43a6d5","No":"#e77b53","Not sure":"#eaa83e"})
    fig.update_layout(template="plotly_dark", paper_bgcolor="#1b202a", plot_bgcolor="#1b202a",
                      margin=dict(l=10,r=10,t=20,b=10), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Future Investment Intention")
    future_col = questions[-1]
    future = clean[future_col].value_counts()
    order = ["Yes", "No", "Not sure"]
    donut_vals = [int(future.get(x, 0)) for x in order]
    fig = go.Figure(data=[go.Pie(labels=order, values=donut_vals, hole=.58,
        marker_colors=["#43a6d5","#e77b53","#eaa83e"], textinfo="label+percent")])
    fig.update_layout(template="plotly_dark", paper_bgcolor="#1b202a", plot_bgcolor="#1b202a",
                      margin=dict(l=10,r=10,t=15,b=10), showlegend=False,
                      annotations=[dict(text=f"{n}<br>respondents", x=.5, y=.5, showarrow=False,
                                        font=dict(size=18, color="#f5f6f8"))])
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Based on: {future_col}")

lower_left, lower_mid, lower_right = st.columns([1.1, 1, 1.2])
with lower_left:
    st.subheader("Most Common 'Yes' Responses")
    yes_counts = [(q, int(clean[q].eq("Yes").sum())) for q in questions]
    yes_counts.sort(key=lambda x: x[1], reverse=True)
    top = yes_counts[:4]
    bar_df = pd.DataFrame({"Survey question":[q if len(q) <= 48 else q[:45]+"…" for q,v in top],
                           "Yes responses":[v for q,v in top]})
    fig = px.bar(bar_df, x="Yes responses", y="Survey question", orientation="h",
                 color="Yes responses", color_continuous_scale=["#5856a6","#43a6d5","#49b6b9"])
    fig.update_layout(template="plotly_dark", paper_bgcolor="#1b202a", plot_bgcolor="#1b202a",
                      coloraxis_showscale=False, margin=dict(l=5,r=5,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

with lower_mid:
    st.subheader("Respondent Awareness Scores")
    score_map = {"Yes": 1.0, "Not sure": 0.5, "No": 0.0}
    scores = clean.apply(lambda col: col.map(score_map)).mean(axis=1, skipna=True).fillna(0) * 100
    st.metric("Average awareness score", f"{scores.mean():.1f}%")
    score_df = pd.DataFrame({"Respondent": np.arange(1, n+1), "Awareness score (%)": scores.to_numpy()})
    fig = px.scatter(score_df, x="Respondent", y="Awareness score (%)",
                     color_discrete_sequence=["#7774c8"])
    fig.update_layout(template="plotly_dark", paper_bgcolor="#1b202a", plot_bgcolor="#1b202a",
                      margin=dict(l=5,r=5,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

with lower_right:
    st.subheader("Respondents by Age Group")
    if age_col:
        age_counts = df[age_col].fillna("Not specified").astype(str).value_counts().reset_index()
        age_counts.columns = ["Age group", "Respondents"]
        fig = px.bar(age_counts, x="Age group", y="Respondents", color="Age group",
                     color_discrete_sequence=["#43a6d5","#eaa83e","#e77b53","#49b6b9","#7774c8"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="#1b202a", plot_bgcolor="#1b202a",
                          showlegend=False, margin=dict(l=5,r=5,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No age column was detected in the uploaded CSV.")

with st.expander("View filtered survey data"):
    st.dataframe(df, use_container_width=True)

st.caption("All charts and metrics update automatically when you change the age filter.")
