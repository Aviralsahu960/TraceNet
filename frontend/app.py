import streamlit as st

st.set_page_config(page_title="TraceNet", layout="wide")

st.title("TraceNet: Mule Ring Detection")

with st.sidebar:
    st.header("Controls")
    st.write("Use the options below to configure the dashboard.")
    refresh_rate = st.slider("Refresh rate (seconds)", 1, 60, 5)
    st.button("Refresh Feed")

st.subheader("Live Transaction Feed")
st.info("Waiting for live transaction data...")

feed_placeholder = st.empty()
feed_placeholder.write("No transactions to display yet.")
