import streamlit as st
from PIL import Image

st.set_page_config(layout="wide", page_title="Global Travel Network")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to bottom, #1a3a5c 0%, #5a89b8 100%);
        margin: 0;
        padding: 0;
    }
    
    .main {
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }
    
    .block-container {
        padding: 2rem;
        max-width: 55%;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# Load and display the image
try:
    image = Image.open("travel_map.png")
    st.image(image, use_container_width=True)
except:
    st.error("Please place 'travel_map.png' in the same directory as this script")