import streamlit as st
import pandas as pd
from ui.components.api_client import fetch_anomalies, fetch_feature_importance
from ui.charts.plotly_charts import anomaly_scatter, feature_importance_bar


def render():
    st.header("⚠️ Anomaly Detection (Isolation Forest)")

    data = fetch_anomalies()
    importance = fetch_feature_importance()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Anomalies", data["total_anomalies"])
    col2.metric("Anomaly Rate", f"{data['anomaly_rate']}%")
    col3.metric(
        "Depression in Anomalies",
        f"{data['depression_in_anomalies']:.1%}",
        delta="vs overall",
    )

    st.divider()
    st.subheader("Anomaly Score Distribution")
    st.plotly_chart(anomaly_scatter(data), use_container_width=True)

    st.divider()
    st.subheader("High-Risk Anomalous Profiles")
    df = pd.DataFrame(data["anomalies"])
    if not df.empty:
        high_risk = df[df["Depression"] == 1].sort_values("anomaly_score")
        st.dataframe(
            high_risk[["Age", "Gender", "Risk_Score", "Sleep_hours",
                        "Financial Stress", "Academic Pressure", "anomaly_score"]]
            .head(50)
            .reset_index(drop=True)
            .style.format({"anomaly_score": "{:.4f}", "Risk_Score": "{:.2f}",
                           "Sleep_hours": "{:.1f}"}),
            use_container_width=True,
        )

    st.divider()
    st.subheader("Feature Importance — RandomForest")
    st.plotly_chart(feature_importance_bar(importance), use_container_width=True)
