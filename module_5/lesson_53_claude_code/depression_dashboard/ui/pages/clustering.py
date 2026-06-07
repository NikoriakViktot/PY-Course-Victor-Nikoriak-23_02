import streamlit as st
import pandas as pd
from ui.components.api_client import fetch_clusters
from ui.charts.plotly_charts import cluster_scatter, cluster_radar


_CLUSTER_LABELS = {
    0: "High Pressure",
    1: "Sleep Deprived",
    2: "Stable / Low Risk",
    3: "Financially Stressed",
}


def render():
    st.header("🧠 Behavioral Clustering (KMeans + PCA)")

    data = fetch_clusters()

    st.caption(
        f"KMeans · {data['n_clusters']} clusters · "
        f"PCA explains {data['explained_variance']:.1%} of variance"
    )

    st.plotly_chart(cluster_scatter(data), use_container_width=True)

    st.divider()
    st.subheader("Cluster Profiles")

    profiles = data["cluster_profiles"]
    profile_df = pd.DataFrame(profiles).T
    profile_df.index = [
        f"Cluster {i} — {_CLUSTER_LABELS.get(int(i), '')}"
        for i in profile_df.index
    ]
    st.dataframe(profile_df.style.format("{:.2f}").background_gradient(cmap="RdYlGn_r"),
                 use_container_width=True)

    st.divider()
    st.subheader("Radar Chart — Cluster Profiles")
    st.plotly_chart(cluster_radar(profiles), use_container_width=True)

    st.divider()
    st.subheader("Cluster Interpretation")
    for cid, label in _CLUSTER_LABELS.items():
        p = profiles.get(str(cid), profiles.get(cid, {}))
        dep = p.get("Depression", 0)
        st.write(
            f"**Cluster {cid} — {label}** | Depression rate: {dep:.1%} | "
            f"Avg Risk Score: {p.get('Risk_Score', 0):.2f}"
        )
