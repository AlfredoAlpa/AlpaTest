import streamlit as st
import pandas as pd
import os
import time
import base64
from fpdf import FPDF

# 1. SETUP PAGINA
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# 2. LOGIN (Invariato)
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.title("🔐 Accesso AlPaTest")
    codice = st.text_input("Codice:", type="password")
    if st.button("ENTRA"):
        if codice.lower() in ["open", "studente01"]:
            st.session_state.autenticato = True
            st.rerun()
    st.stop()

# 3. INIZIALIZZAZIONE STATO (Cruciale per i pulsanti)
if 'vista' not in st.session_state: st.session_state.vista = "TEST"
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()

# Caricamento Discipline
if 'dict_discipline' not in st.session_state:
    try:
        df_disc = pd.read_excel("quiz.xlsx", sheet_name="Discipline")
        st.session_state.dict_discipline = pd.Series(df_disc.Disciplina.values, index=df_disc.Codice).to_dict()
    except: st.session_state.dict_discipline = {}

# 4. FUNZIONI LOGICHE
def importa_quesiti():
    try:
        df = pd.read_excel("quiz.xlsx", sheet_name=0)
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        frames = []
        for i in range(len(st.session_state.dict_discipline)):
            d = st.session_state.get(f"key_da_{i}","")
            a = st.session_state.get(f"key_a_{i}","")
            if str(d).isdigit() and str(a).isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice = 0
            st.session_state.risposte_date = {}
            st.session_state.fase = "PROVA"
    except Exception as e: st.error(f"Errore: {e}")

def cambia_domanda(direzione):
    if direzione == "succ":
        if st.session_state.indice < len(st.session_state.df_filtrato) - 1:
            st.session_state.indice += 1
    elif direzione == "prec":
        if st.session_state.indice > 0:
            st.session_state.indice -= 1

# 5. LAYOUT APPLICATIVO
st.markdown("<style>.stApp { background: #0D1B2A; color: white; }</style>", unsafe_allow_html=True)

if st.session_state.vista == "TEST":
    # --- SCHERMATA FINALE ---
    if st.session_state.fase == "CONFERMA":
        st.warning("### ❓ Sei sicuro di voler consegnare?")
        if st.button("Sì, CONSEGNA"):
            st.session_state.fase = "CONCLUSIONE"; st.rerun()
        if st.button("No, TORNA AL TEST"):
            st.session_state.fase = "PROVA"; st.rerun()
        st.stop()

    if st.session_state.fase == "CONCLUSIONE":
        st.balloons()
        st.success("### Test Completato!")
        st.write(f"Hai risposto a {len(st.session_state.risposte_date)} domande su {len(st.session_state.df_filtrato)}")
        if st.button("Ricomincia"):
            st.session_state.clear(); st.rerun()
        st.stop()

    # --- SCHERMATA TEST ---
    col1, col2 = st.columns([8, 2])
    with col1: st.title("🏆 AlPaTest")
    with col2: 
        if st.button("📚 DISPENSE"):
            st.session_state.vista = "STUDIO"; st.rerun()

    st.divider()

    c_sx, c_ct, c_dx = st.columns([2, 6, 4])

    with c_sx:
        st.subheader("Navigazione")
        if not st.session_state.df_filtrato.empty:
            # Sincronizziamo il radio con l'indice
            lista_q = [f"Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            idx_sel = st.radio("Seleziona:", lista_q, index=st.session_state.indice, key="nav_manuale")
            st.session_state.indice = lista_q.index(idx_sel)

    with c_ct:
        if not st.session_state.df_filtrato.empty:
            curr_idx = st.session_state.indice
            row = st.session_state.df_filtrato.iloc[curr_idx]
            
            st.subheader(f"Domanda {curr_idx + 1}")
            st.info(row['Domanda'])
            
            opts = [f"A) {row['opz_A']}", f"B) {row['opz_B']}", f"C) {row['opz_C']}", f"D) {row['opz_D']}"]
            
            # Gestione risposta
            r_prec = st.session_state.risposte_date.get(curr_idx)
            idx_r = ["A", "B", "C", "D"].index(r_prec) if r_prec else None
            
            scelta = st.radio("La tua risposta:", opts, index=idx_r, key=f"r_{curr_idx}")
            if scelta:
                st.session_state.risposte_date[curr_idx] = scelta[0]

            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1: st.button("⬅️ Prec", on_click=cambia_domanda, args=("prec",), use_container_width=True)
            with b2: 
                if st.button("🏁 CONSEGNA", type="primary", use_container_width=True):
                    st.session_state.fase = "CONFERMA"; st.rerun()
            with b3: st.button("Succ ➡️", on_click=cambia_domanda, args=("succ",), use_container_width=True)
        else:
            st.info("Carica i quesiti per iniziare.")

    with c_dx:
        st.subheader("Discipline")
        if st.session_state.dict_discipline:
            for i, (cod, testo) in enumerate(st.session_state.dict_discipline.items()):
                st.write(f"**{testo}**")
                col_a, col_b = st.columns(2)
                st.session_state[f"key_da_{i}"] = col_a.text_input("Da", key=f"da_{i}", label_visibility="collapsed")
                st.session_state[f"key_a_{i}"] = col_b.text_input("A", key=f"a_{i}", label_visibility="collapsed")
        st.button("📥 IMPORTA QUESITI", on_click=importa_quesiti, use_container_width=True)

else:
    # --- AREA DISPENSE ---
    st.title("📚 Studio Dispense")
    if st.button("⬅️ TORNA AL TEST"):
        st.session_state.vista = "TEST"; st.rerun()
    
    st.divider()
    # Logica per visualizzare PDF (quella stabile con download button)
    if os.path.exists("dispense"):
        files = [f for f in os.listdir("dispense") if f.endswith(".pdf")]
        scelta_pdf = st.selectbox("Scegli un file:", files)
        if scelta_pdf:
            path = os.path.join("dispense", scelta_pdf)
            with open(path, "rb") as f:
                st.download_button("Scarica/Apri PDF", f, file_name=scelta_pdf)
