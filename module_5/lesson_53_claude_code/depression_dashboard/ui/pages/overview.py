import streamlit as st
import pandas as pd
from ui.components.api_client import fetch_summary, fetch_burnout
from ui.charts.plotly_charts import depression_pie, burnout_bar


def render():
    st.header("📊 Dataset Overview")

    summary = fetch_summary()
    burnout = fetch_burnout()

    # ── KPI cards ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", f"{summary['total_records']:,}")
    c2.metric("Depressed", f"{summary['depression_yes']:,}",
              delta=f"{summary['depression_rate']}%", delta_color="inverse")
    c3.metric("Avg Age", summary["avg_age"])
    c4.metric("Avg Sleep", f"{summary['avg_sleep_hours']:.1f}h")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(depression_pie(summary), use_container_width=True)
    with col2:
        gender = summary["gender_distribution"]
        st.subheader("Gender Distribution")
        for k, v in gender.items():
            st.progress(int(v / summary["total_records"] * 100), text=f"{k}: {v:,}")

    st.divider()
    st.subheader("Tech Burnout Dataset — PHQ-9 Severity")
    st.caption("100,000 tech workers · Mental Health Burnout 2026")
    col3, col4, col5 = st.columns(3)
    col3.metric("Avg PHQ-9 Score", burnout["avg_phq9"])
    col4.metric("Avg GAD-7 Score", burnout["avg_gad7"])
    col5.metric("Avg Burnout Score", burnout["avg_burnout"])

    col6, col7 = st.columns(2)
    with col6:
        st.plotly_chart(
            burnout_bar(burnout, "phq9_category_counts", "PHQ-9 Category Distribution"),
            use_container_width=True,
        )
    with col7:
        st.plotly_chart(
            burnout_bar(burnout, "burnout_level_counts", "Burnout Level Distribution"),
            use_container_width=True,
        )

    st.divider()
    st.subheader("Feature Statistics")
    stats_df = pd.DataFrame(summary["feature_stats"]).T
    st.dataframe(stats_df.style.format("{:.2f}"), use_container_width=True)
