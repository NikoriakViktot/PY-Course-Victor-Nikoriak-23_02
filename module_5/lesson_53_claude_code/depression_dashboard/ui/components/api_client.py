import requests
import streamlit as st
import os

BACKEND = os.getenv("BACKEND_URL", "http://localhost:5050")


def _get(endpoint: str) -> dict:
    url = f"{BACKEND}{endpoint}"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error(f"Cannot connect to backend at {BACKEND}. Is Flask running?")
        st.stop()
    except Exception as e:
        st.error(f"API error [{endpoint}]: {e}")
        st.stop()


def _post(endpoint: str, payload: dict) -> dict:
    url = f"{BACKEND}{endpoint}"
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error(f"Cannot connect to backend at {BACKEND}. Is Flask running?")
        st.stop()
    except Exception as e:
        st.error(f"API error [{endpoint}]: {e}")
        st.stop()


@st.cache_data(ttl=300, show_spinner="Loading summary…")
def fetch_summary() -> dict:
    return _get("/api/summary")


@st.cache_data(ttl=300, show_spinner="Loading correlations…")
def fetch_correlations() -> dict:
    return _get("/api/correlations")


@st.cache_data(ttl=300, show_spinner="Loading groups…")
def fetch_groups() -> dict:
    return _get("/api/groups")


@st.cache_data(ttl=300, show_spinner="Loading clusters…")
def fetch_clusters() -> dict:
    return _get("/api/clusters")


@st.cache_data(ttl=300, show_spinner="Loading anomalies…")
def fetch_anomalies() -> dict:
    return _get("/api/anomalies")


@st.cache_data(ttl=300, show_spinner="Loading feature importance…")
def fetch_feature_importance() -> dict:
    return _get("/api/feature-importance")


@st.cache_data(ttl=300, show_spinner="Loading burnout data…")
def fetch_burnout() -> dict:
    return _get("/api/burnout")


def post_predict(payload: dict) -> dict:
    return _post("/api/predict", payload)


def post_train() -> dict:
    return _post("/api/train", {})
