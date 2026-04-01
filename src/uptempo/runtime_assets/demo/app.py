"""Uptempo Streamlit UI — built-in runtime companion module."""

from __future__ import annotations

import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Uptempo",
    page_icon="🎵",
    layout="wide",
)


# ── Sidebar: schema source selection ────────────────────────────────
st.sidebar.title("Uptempo")
schema_source = st.sidebar.radio(
    "Schema source",
    ["Upload file", "Select existing"],
)

if schema_source == "Upload file":
    uploaded = st.sidebar.file_uploader(
        "Upload a schema file",
        type=["proto", "thrift", "json", "yaml"],
    )
else:
    # TODO: fetch available schemas from FastAPI backend
    st.sidebar.selectbox("Available schemas", ["(none)"])


# ── Main area ───────────────────────────────────────────────────────
st.title("Schema Explorer")

tab_structure, tab_test = st.tabs(["Structure", "Test Panel"])

with tab_structure:
    st.info("Upload or select a schema to visualise its structure.")
    # TODO: render tree view / table of services, methods, messages
    # using data from GET {API_BASE}/schemas/{schema_id}

with tab_test:
    st.info("Send test requests to the FastAPI backend.")
    # TODO: interactive form → POST {API_BASE}/schemas/{schema_id}/invoke
    endpoint = st.text_input("Endpoint", value=f"{API_BASE}/health")
    if st.button("Send"):
        import httpx

        try:
            resp = httpx.get(endpoint, timeout=5.0)
            st.json(resp.json())
        except httpx.HTTPError as exc:
            st.error(f"Request failed: {exc}")
