# Depression Analytics Platform

Production-style mental health analytics system.

## Architecture

```
depression_dashboard/
├── backend/                  ← Flask REST API
│   ├── app.py                   app factory
│   ├── config.py                paths, ports, ML params
│   ├── routes/
│   │   ├── analytics.py         /api/summary, /api/correlations, /api/groups, /api/burnout
│   │   └── ml.py                /api/predict, /api/clusters, /api/anomalies, /api/train
│   ├── services/
│   │   ├── data_service.py      data loading + feature engineering (cached)
│   │   ├── analytics_service.py correlation, groupby, burnout stats
│   │   └── ml_service.py        RandomForest · KMeans · IsolationForest · PCA
│   └── utils/logger.py
│
├── ui/                       ← Streamlit dashboard
│   ├── app.py                   tab navigation
│   ├── pages/
│   │   ├── overview.py          KPI cards, pie chart, burnout stats
│   │   ├── correlations.py      heatmap, correlation bars, group charts
│   │   ├── clustering.py        PCA scatter, radar chart, cluster profiles
│   │   ├── anomalies.py         isolation forest results, feature importance
│   │   └── prediction.py        interactive prediction form + gauge chart
│   ├── charts/plotly_charts.py  all Plotly figure factories
│   └── components/api_client.py requests wrapper + st.cache_data
│
├── data/                     ← CSV datasets (gitignored if large)
├── models/                   ← Saved pkl artifacts (auto-created)
├── requirements.txt
├── Dockerfile.backend
├── Dockerfile.streamlit
└── docker-compose.yml
```

## Datasets

| Dataset | Rows | Purpose |
|---------|------|---------|
| Student Depression Dataset | 27,901 | Primary ML target (binary depression label) |
| Sleep Health & Lifestyle | 373 | Sleep/stress cross-reference |
| Mental Health Burnout Tech 2026 | 100,000 | PHQ-9 / GAD-7 burnout benchmarks |

## Feature Engineering

| Feature | Formula |
|---------|---------|
| `Risk_Score` | `0.3×academic_pressure + 0.3×financial_stress + 0.2×work_hours − 0.2×sleep_hours` |
| `Pressure_Sum` | `academic_pressure + work_pressure` |
| `Satisfaction_Sum` | `study_satisfaction + job_satisfaction` |
| `Sleep_deficit` | `max(0, 7 − sleep_hours)` |
| `Sleep_hours` | Mapped from text → float midpoints |

## ML Pipeline

| Model | Purpose |
|-------|---------|
| `RandomForestClassifier` | Depression prediction (binary) |
| `KMeans(k=4)` | Behavioral clustering |
| `IsolationForest` | High-risk anomaly detection |
| `PCA(n=2)` | Cluster visualization projection |

## Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Flask backend (auto-trains models on first run)
python run_backend.py
# → http://localhost:5050

# 3. Start Streamlit (new terminal)
streamlit run ui/app.py
# → http://localhost:8501
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/summary` | Dataset KPIs and stats |
| GET | `/api/correlations` | Correlation matrix + top predictors |
| GET | `/api/groups` | Depression rate by sleep / diet / stress / gender |
| GET | `/api/burnout` | PHQ-9 / GAD-7 distributions |
| POST | `/api/predict` | Depression probability for given profile |
| GET | `/api/clusters` | KMeans cluster assignments + PCA coords |
| GET | `/api/anomalies` | IsolationForest outliers |
| GET | `/api/feature-importance` | RandomForest feature importance |
| POST | `/api/train` | Re-train all models |

## Docker

```bash
docker compose up --build
# backend → http://localhost:5050
# dashboard → http://localhost:8501
```

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| 📊 Overview | KPI cards, depression pie, burnout PHQ-9, feature stats table |
| 📈 Correlations | Heatmap, correlation bar chart, group analysis charts |
| 🧠 Clustering | PCA scatter, radar chart, cluster profile table |
| ⚠️ Anomaly Detection | Isolation Forest scatter, high-risk profiles, feature importance |
| 🤖 Prediction | Interactive sliders → gauge chart → risk level |
