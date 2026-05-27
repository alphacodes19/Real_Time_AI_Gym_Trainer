import streamlit as st
from services.auth.login_wall import render_login_wall

def main():
    st.set_page_config(
        page_icon = "🏋️‍♂️",
        page_title = "AI Real-Time Gym Trainer",
        layout = "centered",
        initial_sidebar_state = "expanded"
    )
    
    if not render_login_wall():
        return
    
    st.write("hello")
    if __name__ == "__main__":
        main()