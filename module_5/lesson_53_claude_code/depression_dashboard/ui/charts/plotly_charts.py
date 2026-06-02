import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

PALETTE = px.colors.qualitative.Set2
DEPRESSION_COLORS = {0: "#4CAF50", 1: "#E53935"}


def depression_pie(summary: dict) -> go.Figure:
    labels = ["Not Depressed", "Depressed"]
    values = [summary["depression_no"], summary["depression_yes"]]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=["#4CAF50", "#E53935"],
        hole=0.45, textinfo="percent+label",
    ))
    fig.update_layout(title="Depression Distribution", margin=dict(t=40, b=0))
    return fig


def age_histogram(summary: dict) -> go.Figure:
    stats = summary["feature_stats"]["Age"]
    x = np.linspace(stats["min"], stats["max"], 50)
    fig = go.Figure(go.Bar(
        x=list(summary["feature_stats"]["Age"].keys()),
        y=list(summary["feature_stats"]["Age"].values()),
        marker_color="#5C6BC0",
    ))
    fig.update_layout(title="Age Statistics", xaxis_title="Stat", yaxis_title="Value")
    return fig


def correlation_heatmap(corr_data: dict) -> go.Figure:
    features = corr_data["features"]
    matrix = pd.DataFrame(corr_data["matrix"]).loc[features, features]
    fig = px.imshow(
        matrix, text_auto=".2f", color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1, aspect="auto",
        title="Feature Correlation Matrix",
    )
    fig.update_layout(margin=dict(t=60))
    return fig


def depression_correlation_bar(corr_data: dict) -> go.Figure:
    dep_corr = corr_data["with_depression"]
    df = pd.DataFrame(
        {"Feature": list(dep_corr.keys()), "Correlation": list(dep_corr.values())}
    ).sort_values("Correlation", key=abs, ascending=True)
    colors = ["#E53935" if v > 0 else "#1565C0" for v in df["Correlation"]]
    fig = go.Figure(go.Bar(
        x=df["Correlation"], y=df["Feature"], orientation="h",
        marker_color=colors,
    ))
    fig.update_layout(
        title="Correlation with Depression",
        xaxis_title="Pearson r", yaxis_title="",
        height=420, margin=dict(l=160),
    )
    return fig


def group_bar(group_data: dict, key: str, title: str) -> go.Figure:
    data = group_data.get(key, {})
    if not data:
        return go.Figure()
    categories = list(data.keys())
    values = [
        v["rate"] if isinstance(v, dict) else v
        for v in data.values()
    ]
    fig = go.Figure(go.Bar(
        x=categories, y=values,
        marker_color="#7E57C2", text=[f"{v:.1%}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title=title, yaxis_title="Depression Rate",
        yaxis_tickformat=".0%", margin=dict(t=50),
    )
    return fig


def cluster_scatter(cluster_data: dict) -> go.Figure:
    points = pd.DataFrame(cluster_data["points"])
    fig = px.scatter(
        points, x="pca_x", y="pca_y",
        color=points["cluster"].astype(str),
        symbol=points["Depression"].astype(str),
        hover_data=["Age", "Risk_Score"],
        color_discrete_sequence=PALETTE,
        title=f"KMeans Clusters — PCA projection "
              f"(explained variance {cluster_data['explained_variance']:.1%})",
        labels={"color": "Cluster", "symbol": "Depressed"},
    )
    fig.update_traces(marker=dict(size=5, opacity=0.7))
    fig.update_layout(height=480)
    return fig


def cluster_radar(profiles: dict) -> go.Figure:
    features = ["Age", "Risk_Score", "Sleep_hours", "Financial Stress",
                "Academic Pressure", "Depression"]
    fig = go.Figure()
    for cluster_id, vals in profiles.items():
        r = [vals.get(f, 0) for f in features]
        fig.add_trace(go.Scatterpolar(
            r=r + [r[0]], theta=features + [features[0]],
            fill="toself", name=f"Cluster {cluster_id}",
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Cluster Profiles (Radar)",
        height=420,
    )
    return fig


def anomaly_scatter(anomaly_data: dict) -> go.Figure:
    df = pd.DataFrame(anomaly_data["anomalies"])
    if df.empty:
        return go.Figure()
    fig = px.scatter(
        df, x="anomaly_score", y="Risk_Score",
        color=df["Depression"].astype(str),
        size_max=8, opacity=0.7,
        color_discrete_map={"0": "#4CAF50", "1": "#E53935"},
        title="Anomaly Score vs Risk Score",
        labels={"color": "Depressed", "anomaly_score": "Isolation Score"},
        hover_data=["Age", "Financial Stress", "Sleep_hours"],
    )
    return fig


def feature_importance_bar(importance: dict) -> go.Figure:
    df = pd.DataFrame(
        {"Feature": list(importance.keys()), "Importance": list(importance.values())}
    ).head(12)
    fig = go.Figure(go.Bar(
        x=df["Importance"], y=df["Feature"], orientation="h",
        marker_color="#FF7043",
    ))
    fig.update_layout(
        title="Top Feature Importances (RandomForest)",
        xaxis_title="Importance", yaxis_title="",
        height=400, margin=dict(l=160),
    )
    return fig


def burnout_bar(burnout_data: dict, key: str, title: str) -> go.Figure:
    data = burnout_data.get(key, {})
    fig = go.Figure(go.Bar(
        x=list(data.keys()), y=list(data.values()),
        marker_color="#26A69A", text=list(data.values()),
        textposition="outside",
    ))
    fig.update_layout(title=title, yaxis_title="Count")
    return fig
