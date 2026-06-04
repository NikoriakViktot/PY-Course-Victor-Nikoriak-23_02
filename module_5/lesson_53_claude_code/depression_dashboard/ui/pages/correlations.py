import streamlit as st
from ui.components.api_client import fetch_correlations, fetch_groups
from ui.charts.plotly_charts import (
    correlation_heatmap, depression_correlation_bar, group_bar,
)


def render():
    st.header("📈 Correlation & Group Analytics")

    corr = fetch_correlations()
    groups = fetch_groups()

    st.subheader("Correlation Matrix")
    st.plotly_chart(correlation_heatmap(corr), use_container_width=True)

    st.divider()
    st.subheader("Top Predictors of Depression")
    st.plotly_chart(depression_correlation_bar(corr), use_container_width=True)

    top3 = list(corr["with_depression"].items())[:3]
    st.info(
        "**Strongest positive predictors:** "
        + " · ".join(f"**{k}** ({v:+.2f})" for k, v in top3 if v > 0)
    )

    st.divider()
    st.subheader("Depression Rate by Group")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            group_bar(groups, "by_sleep", "Depression Rate by Sleep Duration"),
            use_container_width=True,
        )
        st.plotly_chart(
            group_bar(groups, "by_gender", "Depression Rate by Gender"),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            group_bar(groups, "by_diet", "Depression Rate by Dietary Habits"),
            use_container_width=True,
        )
        st.plotly_chart(
            group_bar(groups, "by_financial_stress", "Depression Rate by Financial Stress"),
            use_container_width=True,
        )
