import streamlit as st
import plotly.graph_objects as go
from ui.components.api_client import post_predict, post_train


def _gauge(prob: float, label: str) -> go.Figure:
    color = "#E53935" if prob >= 0.5 else "#FFA726" if prob >= 0.3 else "#4CAF50"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(prob * 100, 1),
        title={"text": f"Depression Probability<br><sub>{label}</sub>"},
        delta={"reference": 50, "increasing": {"color": "#E53935"},
               "decreasing": {"color": "#4CAF50"}},
        gauge={
            "axis": {"range": [0, 100], "ticksuffix": "%"},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30], "color": "#E8F5E9"},
                {"range": [30, 60], "color": "#FFF3E0"},
                {"range": [60, 100], "color": "#FFEBEE"},
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "value": 50},
        },
        number={"suffix": "%"},
    ))
    fig.update_layout(height=280, margin=dict(t=60, b=20))
    return fig


_SLEEP_MAP = {
    "Less than 5 hours": 4.0,
    "5-6 hours": 5.5,
    "7-8 hours": 7.5,
    "More than 8 hours": 9.0,
}

_DIETARY_MAP = {"Unhealthy": 0, "Moderate": 1, "Healthy": 2}


def render():
    st.header("🤖 Depression Risk Prediction")
    st.caption("RandomForest classifier trained on 27,901 student records")

    with st.form("prediction_form"):
        st.subheader("Personal Profile")
        c1, c2, c3 = st.columns(3)
        age = c1.slider("Age", 15, 60, 22)
        gender = c2.selectbox("Gender", ["Male", "Female"])
        sleep_label = c3.selectbox("Sleep Duration", list(_SLEEP_MAP.keys()), index=1)

        st.subheader("Academic & Work")
        c4, c5, c6 = st.columns(3)
        academic_pressure = c4.slider("Academic Pressure (0-5)", 0.0, 5.0, 3.0, 0.5)
        work_pressure = c5.slider("Work Pressure (0-5)", 0.0, 5.0, 1.0, 0.5)
        work_hours = c6.slider("Work/Study Hours per day", 0.0, 16.0, 6.0, 0.5)

        st.subheader("Lifestyle & Wellbeing")
        c7, c8, c9 = st.columns(3)
        cgpa = c7.slider("CGPA (0-10)", 0.0, 10.0, 7.5, 0.1)
        study_sat = c8.slider("Study Satisfaction (0-5)", 0.0, 5.0, 3.0, 0.5)
        job_sat = c9.slider("Job Satisfaction (0-5)", 0.0, 5.0, 3.0, 0.5)

        c10, c11, c12 = st.columns(3)
        financial_stress = c10.slider("Financial Stress (1-5)", 1.0, 5.0, 2.0, 0.5)
        diet_label = c11.selectbox("Dietary Habits", list(_DIETARY_MAP.keys()), index=1)
        family_history = c12.checkbox("Family History of Mental Illness")
        suicidal_thoughts = st.checkbox("History of Suicidal Thoughts")

        submitted = st.form_submit_button("🔮 Predict Depression Risk", type="primary")

    if submitted:
        sleep_hours = _SLEEP_MAP[sleep_label]
        dietary_enc = _DIETARY_MAP[diet_label]
        gender_enc = 1 if gender == "Female" else 0
        risk_score = (
            academic_pressure * 0.3
            + financial_stress * 0.3
            + work_hours * 0.2
            - sleep_hours * 0.2
        )
        payload = {
            "Age": age,
            "Academic Pressure": academic_pressure,
            "Work Pressure": work_pressure,
            "CGPA": cgpa,
            "Study Satisfaction": study_sat,
            "Job Satisfaction": job_sat,
            "Sleep_hours": sleep_hours,
            "Work/Study Hours": work_hours,
            "Financial Stress": financial_stress,
            "Gender_enc": gender_enc,
            "Family_History_enc": int(family_history),
            "Suicidal_enc": int(suicidal_thoughts),
            "Dietary_enc": dietary_enc,
            "Risk_Score": risk_score,
            "Pressure_Sum": academic_pressure + work_pressure,
            "Satisfaction_Sum": study_sat + job_sat,
            "Sleep_deficit": max(0.0, 7.0 - sleep_hours),
        }

        with st.spinner("Running inference …"):
            result = post_predict(payload)

        st.divider()
        st.subheader("Prediction Result")

        risk_colors = {"Low": "green", "Medium": "orange", "High": "red"}
        risk = result["risk_level"]
        st.markdown(
            f"### Risk Level: :{risk_colors[risk]}[{risk}]",
            unsafe_allow_html=False,
        )

        st.plotly_chart(_gauge(result["probability_depressed"], risk), use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric("Probability Depressed", f"{result['probability_depressed']:.1%}")
        col2.metric("Probability Not Depressed", f"{result['probability_not_depressed']:.1%}")

        if risk == "High":
            st.error(
                "⚠️ High risk profile detected. Key factors: financial stress, "
                "sleep deficit, academic pressure. Consider professional consultation."
            )
        elif risk == "Medium":
            st.warning("Moderate risk. Monitor sleep, stress, and workload.")
        else:
            st.success("Low risk profile. Keep maintaining healthy habits.")

    st.divider()
    with st.expander("🔄 Re-train Models"):
        if st.button("Train all models (takes ~30s)", type="secondary"):
            with st.spinner("Training RandomForest, KMeans, IsolationForest …"):
                result = post_train()
            st.success(f"Training complete! AUC={result['metrics']['auc']:.4f} | "
                       f"Accuracy={result['metrics']['accuracy']:.4f}")
