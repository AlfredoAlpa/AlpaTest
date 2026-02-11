import streamlit as st
import pandas as pd
import os
import time
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# --- LOGIN ROBUSTO E RESPONSIVE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] > div:has(.titolo-box) {
            border: 3px solid #FFD700 !important;
            border-radius: 20px !important;
            padding: 50px 20px !important;
            background-color: rgba(0, 0, 0, 0.5) !important;
            width: 95% !important;
            max-width: 550px !important;
            margin: 40px auto !important;
            text-align: center !important;
        }
        .titolo-box {
            color: #FFD700 !important;
            font-size: clamp(1.6rem, 7vw, 2.3rem) !important;
            font-weight: 900 !important;
            display: block !important;
            margin-bottom: 10px !important;
        }
        .istruzione-box {
            color: white !important;
            font-size: 1.2rem !important;
            display: block !important;
            margin-bottom: 25px !important;
        }
        div.stButton > button {
            width: 16
