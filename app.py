# Alpa2 - Versione Stabile con Logout, Promo e Scudo PDF
import streamlit as st
import pandas as pd
import os
import base64
import time
from fpdf import FPDF

# 1. CONFIGURAZIONE E LARGHEZZA UTILE
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# --- PROTEZIONE AVANZATA (CSS + JS) ---
st.markdown("""
    <style>
    [data-testid="stAppViewBlockContainer"] { padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); } 
    .logo-style { font-family: 'Georgia', serif; font-size: 3.5rem !important; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    
    /* 1. TESTO QUESITO E RISPOSTE */
    .quesito-style { color: #FFEB3B !important; font-size: 2rem !important; font-weight: bold !important; line-height: 1.4 !important; }
    div[data-testid="stRadio"] label p { font-size: 1.5rem !important; color: white !important; }
    
    /* 2. CONFIGURAZIONE (DESTRA) */
    .nome-materia { font-size: 1.15rem !important; color: #FFD700 !important; font-weight: bold !important; margin-top: 15px !important; }
    
    div[data-testid="stTextInput"] div[data-baseweb="input"] { 
        background-color: black !important; 
        border: 2px solid #FFD700 !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stTextInput"] input { color: #00FF00 !important; font-weight: bold !important; text-align: center !important; }

    /* 3. PULSANTI */
    .stButton button { font-size: 1.25rem !important; height: 3.2rem !important; font-weight: bold !important; border-radius: 10px !important; }

    /* FIX TESTO NERO SU PROMO */
    div[data-testid="stColumn"]:nth-of-type(2) button[kind="primary"] p {
        color: black !important;
        font-weight: 900 !important;
    }

    html, body, [data-testid="stAppViewBlockContainer"], * {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
    }
    
    /* LO SCUDO PER IL PDF */
    .container-pdf { position: relative; width: 100%; height: 800px; }
    .overlay-stop-popout { 
        position: absolute; 
        top: 0; 
        right: 0; 
        width: 180px; 
        height: 80px; 
        z-index: 99999; 
        background: transparent; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DATI ---
def get_sheet_data(gid):
    try:
        base_url = st.secrets["gsheets_url"].split("/edit")[0]
        csv_url = f"{base_url}/export?format=csv&gid={gid}"
        return pd.read_csv(csv_url)
    except Exception as e: return pd.DataFrame()

# --- INIZIALIZZAZIONE ---
if 'autenticato' not in st.session_state: st.session_state.autenticato = False
if 'is_promo' not in st.session_state: st.session_state.is_promo = False 
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'pdf_id_selezionato' not in st.session_state: st.session_state.pdf_id_selezionato = None
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None

# --- FUNZIONI ---
def importa_quesiti():
    try:
        gid = "326583620" if st.session_state.is_promo else "0" 
        df = get_sheet_data(gid)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        num = len(dict_discipline)
        frames = [df.iloc[int(st.session_state[f"da_{i}"])-1 : int(st.session_state[f"a_{i}"])] for i in range(num) if st.session_state.get(f"da_{i}","").isdigit()]
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice, st.session_state.risposte_date, st.session_state.start_time = 0, {}, time.time()
    except Exception as e: st.error(f"Errore: {e}")

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, 1800 - (time.time() - st.session_state.start_time))
        st.markdown(f'<p style="color:white; font-size:1.5rem; text-align:right;">⏱️ {int(rimanente//60):02d}:{int(rimanente%60):02d}</p>', unsafe_allow_html=True)

dict_discipline = carica_discipline() if 'carica_discipline' in locals() else {}
# (Nota: assicurati che carica_discipline() sia definita come nel tuo codice originale)

# --- LOGIN ---
if not st.session_state.autenticato:
    st.markdown('<div style="text-align: center; max-width: 650px; margin: 40px auto;"><h1 style="color: #FFD700; font-size: 2.4rem;">🔐 Accesso AlPaTest</h1></div>', unsafe_allow_html=True)
    col_full, col_promo = st.columns(2)
    with col_full:
        codice = st.text_input("Codice Full:", type="password", placeholder="Codice")
        if st.button("ENTRA (VERSIONE FULL)", use_container_width=True):
            df_c = get_sheet_data("184205490")
            if not df_c.empty and codice in df_c.iloc[:,0].astype(str).values:
                st.session_state.autenticato = True
                st.session_state.is_promo = False
                st.rerun()
    with col_promo:
        st.write("Vuoi provare il sistema?")
        if st.button("🚀 PROVA LA PROMO GRATUITA", use_container_width=True, type="primary"):
            st.session_state.autenticato, st.session_state.is_promo = True, True
            st.rerun()
    st.stop()

# --- APP PRINCIPALE ---
if st.session_state.pdf_id_selezionato:
    if st.button("⬅️ CHIUDI DISPENSA"): 
        st.session_state.pdf_id_selezionato = None
        st.rerun()
    # IL PDF CON LO SCUDO
    st.markdown(f'''
        <div class="container-pdf">
            <div class="overlay-stop-popout"></div>
            <iframe src="https://drive.google.com/file/d/{st.session_state.pdf_id_selezionato}/preview" width="100%" height="800"></iframe>
        </div>
    ''', unsafe_allow_html=True)
else:
    t1, t2 = st.columns([7, 3])
    with t1: st.markdown(f'<div class="logo-style">AlPaTest {"(PROMO)" if st.session_state.is_promo else ""}</div>', unsafe_allow_html=True)
    with t2: 
        mostra_timer()
        if st.button("🚪 Esci / Cambia Accesso", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    c_sx, c_ct, c_dx = st.columns([2.5, 6.5, 3])
    with c_sx:
        st.write("Navigazione")
        with st.container(height=300):
            if not st.session_state.df_filtrato.empty:
                for i in range(len(st.session_state.df_filtrato)):
                    if st.button(f"Quesito {i+1}", key=f"n_{i}", use_container_width=True): st.session_state.indice = i; st.rerun()
        
        # --- SEZIONE DISPENSE RIPRISTINATA ---
        st.write("---")
        with st.expander("📚 DISPENSE", expanded=True):
            if st.session_state.is_promo:
                st.info("Modalità Promo: Accesso libero.")
                df_disp = get_sheet_data("272698671") 
                if not df_disp.empty:
                    sel = st.selectbox("Seleziona:", df_disp.iloc[:,0].tolist(), index=None)
                    if sel and st.button("📖 APRI"):
                        st.session_state.pdf_id_selezionato = str(df_disp[df_disp.iloc[:,0]==sel].iloc[0,1]).strip()
                        st.rerun()

    with c_ct:
        if not st.session_state.df_filtrato.empty:
            q = st.session_state.df_filtrato.iloc[st.session_state.indice]
            st.markdown(f'<div class="quesito-style">{st.session_state.indice+1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
            opzioni = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
            scelta = st.radio("Risposta:", opzioni, key=f"r_{st.session_state.indice}")
            if scelta: st.session_state.risposte_date[st.session_state.indice] = scelta[0]
            
            # TASTI NAVIGAZIONE RIPRISTINATI
            st.write("---")
            b1, b2, b3 = st.columns(3)
            if b1.button("⬅️ Precedente", use_container_width=True) and st.session_state.indice > 0:
                st.session_state.indice -= 1; st.rerun()
            if b2.button("Successivo ➡️", use_container_width=True) and st.session_state.indice < len(st.session_state.df_filtrato)-1:
                st.session_state.indice += 1; st.rerun()
            if b3.button("🏁 CONSEGNA", use_container_width=True): 
                st.session_state.fase = "FINE"; st.rerun()
        else: st.info("Configura a destra.")

    with c_dx:
        st.write("Configurazione")
        dict_discipline = carica_discipline() # Carica i nomi corretti
        for i, (cod, nome) in enumerate(dict_discipline.items()):
            st.markdown(f"<p class='nome-materia'>{cod}: {nome}</p>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.text_input("da", key=f"da_{i}", label_visibility="collapsed")
            c2.text_input("a", key=f"a_{i}", label_visibility="collapsed")
        st.checkbox("Simulazione", key="simulazione")
        st.button("IMPORTA QUESITI", on_click=importa_quesiti, use_container_width=True, type="primary")
