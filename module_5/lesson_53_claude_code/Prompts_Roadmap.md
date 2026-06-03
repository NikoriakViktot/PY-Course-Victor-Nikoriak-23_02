# 🧠 Depression Analytics Platform — AI Agent Prompts Roadmap

---

# 📦 STAGE 1 — Project Initialization

## 🎯 Goal

Create the project foundation and environment.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior Python Software Architect.

Help me initialize a production-style Python analytics project named:

depression_analytics

Tech stack:
- Flask
- Streamlit
- Pandas
- Plotly
- Scikit-learn

Tasks:
1. Create professional folder structure
2. Create Python virtual environment setup instructions
3. Generate requirements.txt
4. Suggest development workflow
5. Add .gitignore
6. Add README starter
7. Explain WHY each folder exists
8. Explain how real production Python projects are structured

Important:
- Think like a senior backend/data architect
- Use clean architecture principles
- Explain system thinking
- Keep modular structure
```

---

# 🗂 STAGE 2 — Project Structure

## 🎯 Goal

Design architecture before coding.

---

# 🤖 AI AGENT PROMPT

```text
Act as a Senior Software Architect.

Help me design the architecture for a mental health analytics platform.

Tech:
- Flask backend
- Streamlit frontend
- ML pipeline
- Plotly visualization

Generate:
1. Full folder structure
2. Separation of concerns
3. Backend responsibilities
4. Frontend responsibilities
5. ML layer responsibilities
6. Data flow diagram
7. Recommended naming conventions
8. Logging strategy
9. Config strategy

Explain:
- WHY architecture matters
- WHY backend/frontend separation exists
- HOW data flows through the system
```

---

# 📊 STAGE 3 — Dataset Exploration (EDA)

## 🎯 Goal

Understand data deeply.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior Data Scientist.

I have a depression dataset from Kaggle.

Help me perform professional exploratory data analysis (EDA).

Tasks:
1. Load dataset with pandas
2. Analyze missing values
3. Detect categorical and numerical columns
4. Find target variable
5. Detect imbalance
6. Generate statistical summaries
7. Detect potential data quality issues
8. Suggest important visualizations

Explain:
- WHY each analysis step matters
- HOW data scientists think during EDA
- WHAT hidden risks may exist in datasets

Use:
- pandas
- plotly
- matplotlib
- seaborn
```

---

# 📈 STAGE 4 — Visualization

## 🎯 Goal

Transform data into understanding.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior Data Visualization Engineer.

Help me create professional visualizations for a depression analytics platform.

Dataset contains:
- stress
- sleep
- academic pressure
- financial pressure
- depression label

Generate:
1. Distribution charts
2. Correlation heatmaps
3. Boxplots
4. Scatter plots
5. Pie charts
6. Risk visualizations

Requirements:
- Use Plotly
- Use clean professional styling
- Add titles and labels
- Explain what each chart reveals

Teach me:
- WHY visualization matters
- HOW analysts extract patterns visually
- HOW dashboards communicate insights
```

---

# 🧠 STAGE 5 — Feature Engineering

## 🎯 Goal

Create intelligent features.

---

# 🤖 AI AGENT PROMPT

```text
Act as a Senior ML Engineer.

Help me design feature engineering for a depression prediction system.

Dataset contains:
- sleep
- stress
- anxiety
- financial pressure
- study satisfaction
- depression label

Tasks:
1. Suggest meaningful engineered features
2. Explain WHY each feature may help prediction
3. Detect feature interactions
4. Create behavioral indicators
5. Create composite scores
6. Detect possible data leakage

Important:
- Think like a real ML engineer
- Explain domain intelligence
- Explain how feature engineering improves models
- Use pandas and sklearn
```

---

# 🤖 STAGE 6 — Machine Learning

## 🎯 Goal

Train predictive models.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior Machine Learning Engineer.

Help me build a depression prediction pipeline.

Tasks:
1. Create train/test split
2. Encode categorical variables
3. Scale numerical variables
4. Train Logistic Regression
5. Train RandomForest
6. Compare models
7. Calculate metrics:
   - accuracy
   - precision
   - recall
   - F1
   - ROC-AUC
8. Explain overfitting
9. Explain model interpretability

Teach me:
- HOW ML pipelines work
- WHY preprocessing matters
- HOW real ML systems are evaluated
```

---

# 🧩 STAGE 7 — Clustering & Anomaly Detection

## 🎯 Goal

Find hidden behavioral patterns.

---

# 🤖 AI AGENT PROMPT

```text
Act as a Senior Data Scientist specializing in unsupervised learning.

Help me build clustering and anomaly detection for a depression analytics system.

Tasks:
1. Apply KMeans clustering
2. Apply DBSCAN
3. Apply PCA visualization
4. Detect hidden behavioral groups
5. Apply IsolationForest anomaly detection
6. Explain high-risk profiles
7. Visualize clusters

Teach me:
- WHY clustering matters
- HOW anomaly detection works
- HOW unsupervised learning differs from classification
- HOW analysts interpret hidden groups
```

---

# 🌐 STAGE 8 — Flask Backend

## 🎯 Goal

Convert notebook into backend system.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior Backend Engineer.

Help me build a Flask backend for a depression analytics platform.

Requirements:
1. Create Flask application
2. Create modular routes
3. Create services layer
4. Add ML inference endpoint
5. Return JSON responses
6. Add error handling
7. Add logging
8. Use clean architecture

Endpoints:
- /api/summary
- /api/predict
- /api/clusters
- /api/anomalies

Teach me:
- WHY APIs exist
- HOW frontend communicates with backend
- HOW production Flask apps are structured
```

---

# 🎨 STAGE 9 — Streamlit Dashboard

## 🎯 Goal

Create interactive analytics UI.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior Frontend/Data Dashboard Engineer.

Help me build a Streamlit dashboard for depression analytics.

Requirements:
1. Create multi-page dashboard
2. Add sidebar filters
3. Add interactive Plotly charts
4. Add prediction interface
5. Add clustering visualization
6. Add anomaly visualization
7. Add KPI cards
8. Use clean layout

Teach me:
- HOW dashboards are designed
- WHY UX matters in analytics
- HOW users interact with analytics systems
```

---

# 🔥 STAGE 10 — Production Engineering

## 🎯 Goal

Make system production-ready.

---

# 🤖 AI AGENT PROMPT

```text
Act as a Senior Production Engineer.

Help me productionize my Flask + Streamlit analytics platform.

Tasks:
1. Add logging system
2. Add config management
3. Add .env support
4. Add exception handling
5. Add validation
6. Add project settings
7. Add reusable utilities
8. Add monitoring ideas

Teach me:
- WHY production engineering matters
- HOW real systems fail
- HOW observability works
- HOW maintainability is achieved
```

---

# 🐳 STAGE 11 — Docker

## 🎯 Goal

Containerize application.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior DevOps Engineer.

Help me dockerize my analytics platform.

Stack:
- Flask
- Streamlit
- Python 3.12

Tasks:
1. Create Dockerfile
2. Create docker-compose.yml
3. Configure backend container
4. Configure frontend container
5. Configure networking
6. Add environment variables
7. Add volume mounting

Teach me:
- WHY Docker exists
- HOW containers work
- HOW microservices communicate
- HOW deployment works
```

---

# 📚 STAGE 12 — Documentation

## 🎯 Goal

Create professional GitHub-ready project.

---

# 🤖 AI AGENT PROMPT

```text
You are a Senior Technical Writer and Software Architect.

Help me create a professional README.md for my Depression Analytics Platform.

Include:
1. Project overview
2. Architecture diagram
3. Features
4. ML pipeline
5. API endpoints
6. Dashboard screenshots section
7. Installation instructions
8. Docker instructions
9. Project structure
10. Future improvements

Teach me:
- WHY documentation matters
- HOW engineers present projects professionally
- HOW to make portfolio-grade repositories
```

---

# 🌀 FINAL META PROMPT

```text
Act as a Senior Software Architect and Mentor.

I want to learn how to think like a system architect while building a depression analytics platform.

Do NOT only generate code.

Explain:
- architecture decisions
- data flow
- ML integration
- backend/frontend communication
- modular design
- production engineering mindset

I want to transition from:
"writing scripts"
to
"building real systems"
```

