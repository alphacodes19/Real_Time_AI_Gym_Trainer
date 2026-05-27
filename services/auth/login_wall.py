import streamlit as st

def render_login_wall():
    if st.session_state.get("user_id") is not None: