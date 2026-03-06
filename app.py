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

    /* --- FIX CHIRURGICO: SOLO SCRITTA PROMO IN NERO --- */
    div[data-testid="stColumn"]:nth-of-type(2) button[kind="primary"] p {
        color: black !important;
        font-weight: 900 !important;
    }

    /* Tasto Esci */
    div[data-testid="stColumn"]:nth-child(2) .stButton button { color: #FF4B4B !important; border: 2px solid #FF4B4B !important; }

    html, body, [data-testid="stAppViewBlockContainer"], * {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
    }
    
    .container-pdf { position: relative; width: 100%; height: 800px; }
    .overlay-stop-popout { position: absolute; top: 0; right: 0; width: 180px; height: 80px; z-index: 99999; background: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONE RECUPERO DATI GOOGLE SHEETS ---
def get_sheet_data(gid):
    try:
        base_url = st.secrets["gsheets_url"].split("/edit")[0]
        csv_url = f"{base_url}/export?format=csv&gid={gid}"
        return pd.read_csv(csv_url)
    except Exception as e:
        return pd.DataFrame()

# --- INIZIALIZZAZIONE STATO ---
if 'autenticato' not in st.session_state: st.session_state.autenticato = False
if 'is_promo' not in st.session_state: st.session_state.is_promo = False 
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'pdf_id_selezionato' not in st.session_state: st.session_state.pdf_id_selezionato = None
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'punteggi' not in st.session_state: st.session_state.punteggi = {"Corretta": 0.75, "Non Data": 0.0, "Errata": -0.25}
if 'codice_dispense_valido' not in st.session_state: st.session_state.codice_dispense_valido = ""

# --- FUNZIONI UTILI ---
def pulisci_testo(testo):
    if pd.isna(testo) or testo == "": return " "
    repls = {'’':"'",'‘':"'",'“':'"','”':'"','–':'-','à':'a','è':'e','é':'e','ì':'i','ò':'o','ù':'u'}
    t = str(testo)
    for k,v in repls.items(): t = t.replace(k,v)
    return t.encode('latin-1','replace').decode('latin-1')

def calcola_risultati():
    esatte, errate, non_date = 0, 0, 0
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i)
        r_e = str(row['Corretta']).strip()
        if r_u is None: non_date += 1
        elif r_u == r_e: esatte += 1
        else: errate += 1
    punti = (esatte * st.session_state.punteggi["Corretta"]) + (non_date * st.session_state.punteggi["Non Data"]) + (errate * st.session_state.punteggi["Errata"])
    return esatte, errate, non_date, round(punti, 2)

def genera_report_pdf():
    esatte, errate, non_date, punti_tot = calcola_results()
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(100, 10, pulisci_testo("REPORT FINALE - AlPaTest"), ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(100, 8, pulisci_testo(f"PUNTEGGIO TOTALE: {punti_tot}"), ln=True, align='C')
    pdf.ln(10)
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        r_e = str(row['Corretta']).strip()
        pdf.set_font("helvetica", 'B', 10)
        pdf.multi_cell(100, 6, pulisci_testo(f"Domanda {i+1}: {row['Domanda']}"))
        pdf.set_font("helvetica", '', 10)
        pdf.multi_cell(100, 6, pulisci_testo(f"Tua Risposta: {r_u} | Risposta Esatta: {r_e}"))
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 110, pdf.get_y()) 
        pdf.ln(4) 
    return bytes(pdf.output())

# --- LOGIN ---
if not st.session_state.autenticato:
    st.markdown('<div style="text-align: center; max-width: 650px; margin: 40px auto;"><h1 style="color: #FFD700; font-size: 2.4rem;">🔐 Accesso AlPaTest</h1></div>', unsafe_allow_html=True)
    col_full, col_promo = st.columns(2)
    with col_full:
        codice = st.text_input("Codice Full:", type="password", placeholder="Inserisci codice")
        if st.button("ENTRA (VERSIONE FULL)", use_container_width=True):
            df_codici_access = get_sheet_data("184205490")
            if not df_codici_access.empty and codice in df_codici_access.iloc[:,0].astype(str).values:
                st.session_state.autenticato = True
                st.session_state.is_promo = False
                st.rerun()
            else: st.error("Codice errato")
    with col_promo:
        st.write("Vuoi provare il sistema?")
        if st.button("🚀 PROVA LA PROMO GRATUITA", use_container_width=True, type="primary"):
            st.session_state.autenticato = True
            st.session_state.is_promo = True
            st.rerun()
    st.stop()

# --- CARICAMENTO RISORSE ---
@st.cache_data
def carica_discipline():
    df_d = get_sheet_data("652955788") 
    return pd.Series(df_d.Disciplina.values, index=df_d.Codice.astype(str)).to_dict() if not df_d.empty else {}

dict_discipline = carica_discipline()

def importa_quesiti():
    try:
        gid_quesiti = "326583620" if st.session_state.is_promo else "0" 
        df = get_sheet_data(gid_quesiti)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        num_discipline = len(dict_discipline)
        frames = [df.iloc[int(st.session_state[f"da_{i}"])-1 : int(st.session_state[f"a_{i}"])] for i in range(num_discipline) if st.session_state.get(f"da_{i}","").isdigit()]
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice, st.session_state.risposte_date, st.session_state.start_time = 0, {}, time.time()
    except Exception as e: st.error(f"Errore: {e}")

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, 1800 - (time.time() - st.session_state.start_time))
        st.markdown(f'<p style="color:white; font-size:1.5rem; text-align:right;">⏱️ {int(rimanente//60):02d}:{int(rimanente%60):02d}</p>', unsafe_allow_html=True)

# --- VISUALIZZAZIONE ---
if st.session_state.pdf_id_selezionato:
    if st.button("⬅️ CHIUDI DISPENSA"): 
        st.session_state.pdf_id_selezionato = None
        st.rerun()
    st.markdown(f'<iframe src="https://drive.google.com/file/d/{st.session_state.pdf_id_selezionato}/preview" width="100%" height="800"></iframe>', unsafe_allow_html=True)
else:
    t1, t2 = st.columns([7, 3])
    with t1: 
        tit = "AlPaTest (PROMO)" if st.session_state.is_promo else "AlPaTest"
        st.markdown(f'<div class="logo-style">{tit}</div>', unsafe_allow_html=True)
    with t2: 
        mostra_timer()
        if st.button("🚪 Esci / Cambia Accesso", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.fase == "FINE":
        es, er, nd, pt = calcola_risultati()
        st.success(f"### Punteggio Totale: {pt}")
        st.download_button("📥 SCARICA PDF", genera_report_pdf(), "Report.pdf", "application/pdf")
        if st.button("🔄 NUOVA PROVA"): 
            st.session_state.fase = "PROVA"
            st.rerun()
    else:
        c_sx, c_ct, c_dx = st.columns([2.5, 6.5, 3])
        with c_sx:
            st.write("Navigazione")
            if not st.session_state.df_filtrato.empty:
                for i in range(len(st.session_state.df_filtrato)):
                    if st.button(f"Quesito {i+1}", key=f"n_{i}", use_container_width=True): st.session_state.indice = i; st.rerun()
        with c_ct:
            if not st.session_state.df_filtrato.empty:
                q = st.session_state.df_filtrato.iloc[st.session_state.indice]
                st.markdown(f'<div class="quesito-style">{st.session_state.indice+1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
                opzioni = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
                scelta = st.radio("Risposta:", opzioni, key=f"r_{st.session_state.indice}")
                if scelta: st.session_state.risposte_date[st.session_state.indice] = scelta[0]
                
                # RIPRISTINO TASTI PRECEDENTE/SUCCESSIVO/CONSEGNA
                st.write("---")
                b1, b2, b3 = st.columns(3)
                if b1.button("⬅️ Precedente", use_container_width=True) and st.session_state.indice > 0:
                    st.session_state.indice -= 1
                    st.rerun()
                if b2.button("Successivo ➡️", use_container_width=True) and st.session_state.indice < len(st.session_state.df_filtrato)-1:
                    st.session_state.indice += 1
                    st.rerun()
                if b3.button("🏁 CONSEGNA", use_container_width=True): 
                    st.session_state.fase = "FINE"
                    st.rerun()
            else: st.info("Seleziona gli intervalli a destra.")
        with c_dx:
            st.write("Configurazione")
            num_discipline = len(dict_discipline)
            # RIPRISTINO NOME DISCIPLINE SOPRA I BOX
            for i, (cod, nome) in enumerate(dict_discipline.items()):
                st.markdown(f"<p class='nome-materia'>{cod}: {nome}</p>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                c1.text_input("da", key=f"da_{i}", label_visibility="collapsed")
                c2.text_input("a", key=f"a_{i}", label_visibility="collapsed")
            st.checkbox("Simulazione", key="simulazione")
            st.button("IMPORTA QUESITI", on_click=importa_quesiti, use_container_width=True, type="primary")
