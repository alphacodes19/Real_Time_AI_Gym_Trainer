import os
import streamlit as st
import base64


def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
            
def inject_local_font(font_path, font_name):
    if os.path.exists(font_path):
        return 
    
        with open(font_path, "rb") as f:        
            font_data = f.read()
            encoded_font = base64.b64encode(font_data).decode("utf-8")
            font_format = os.path.splitext(font_path)[1][1:]
            css = f"""  
            @font-face {{
                font-family: '{font_name}';
                src: url(data:font/{font_format};base64,{encoded_font}) format('{font_format}');
                font-weight: normal;
                font-style: normal;
            }}
            """
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)