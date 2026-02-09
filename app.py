import streamlit as st
import pandas as pd
import os
import time
from fpdf import FPDF

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# 2. LOGIN CON BOX CENTRATO
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.markdown("""
        <style>
        .login-container {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 40px;
            border-radius: 20px;
            border: 2px solid #FFD700;
            max-width: 500px;
            margin: 50px auto;
            text-align: center;
        }
        div[data-testid="stTextInput"] input {
            height: 90px !important;
            font-size: 2.5rem !important;
            text-align: center !important;
            border: 2px solid #FFD700 !important;
            background-color: #1A3651 !important;
            color: white !important;
            padding-bottom: 10px !important;
        }
        div[data-testid="stTextInput"] label { display: none !important; }
        div.stButton > button {
            width: 100% !important;
            height: 65px !important;
            font-size: 2rem !important;
            background-color: #FFD700 !important;
            color: black !important;
            font-weight: bold !important;
            margin-top: 25px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#FFD700;">🔐 Accesso AlPaTest</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#FFD700; font-size:1.5rem; font-weight:bold;">Inserisci il codice di accesso:</p>', unsafe_allow_html=True)
    codice = st.text_input("Codice", type="password").strip()
    if st.button("Entra"):
        if codice.lower() in ["open", "studente01"]:
            st.session_state.autenticato = True
            st.rerun()
        else:
            st.error("Codice errato")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 3. CSS E INIZIALIZZAZIONE
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); }
    .logo-style { font-family: 'Georgia', serif; font-size: 3.5rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.6rem !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

if 'fase' not in st.session_state: st.session_state.fase = "CONFIG"
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'indice' not in st.session_state: st.session_state.indice = 0

# 4. FUNZIONI PDF E CALCOLI (LARGHEZZA 100)
def pulisci_testo(testo):
    return str(testo).encode('latin-1', 'replace').decode('latin-1')

def calcola_risultati():
    esatte, errate, non_date = 0, 0, 0
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i)
        r_e = str(row['Corretta']).strip()
        if r_u is None: non_date += 1
        elif r_u == r_e: esatte += 1
        else: errate += 1
    punteggio = (esatte * 0.75) + (errate * -0.25)
    return esatte, errate, non_date, round(punteggio, 2)

def genera_report_pdf():
    esatte, errate, non_date, punti = calcola_risultati()
    pdf = FPDF()
    pdf.add_page()
    # LA TUA LARGHEZZA UTILE
    larghezza_utile = 100 
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(larghezza_utile, 10, "REPORT FINALE ALPA TEST", ln=True)
    pdf.set_font("helvetica", '', 12)
    pdf.cell(larghezza_utile, 10, f"Esatte: {esatte} | Errate: {errate} | Punti: {punti}", ln=True)
    pdf.ln(10)
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        pdf.set_font("helvetica", 'B', 10)
        pdf.multi_cell(larghezza_utile, 6, pulisci_testo(f"{i+1}. {row['Domanda']}"))
        pdf.set_font("helvetica", '', 10)
        pdf.cell(larghezza_utile, 6, pulisci_testo(f"Tua: {r_u} | Corretta: {row['Corretta']}"), ln=True)
        pdf.ln(2)
    return bytes(pdf.output())

# 5. LOGICA PRINCIPALE
st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)

if st.session_state.fase == "CONFIG":
    try:
        df = pd.read_excel("quiz.xlsx")
        materie = df['Materia'].unique().tolist()
        
        with st.sidebar:
            st.title("⚙️ Impostazioni")
            materia_scelta = st.selectbox("Scegli Materia", materie)
            n_domande = st.number_input("Numero Domande", 5, 100, 20)
            tempo_min = st.slider("Minuti", 1, 60, 10)
            
            if st.button("🚀 INIZIA TEST"):
                st.session_state.df_filtrato = df[df['Materia'] == materia_scelta].sample(n_domande).reset_index(drop=True)
                st.session_state.fase = "QUIZ"
                st.session_state.inizio_test = time.time()
                st.session_state.fine_test = st.session_state.inizio_test + (tempo_min * 60)
                st.rerun()
    except Exception as e:
        st.error(f"Errore caricamento file: {e}")

elif st.session_state.fase == "QUIZ":
    t_rimanente = int(st.session_state.fine_test - time.time())
    if t_rimanente <= 0:
        st.session_state.fase = "RISULTATI"
        st.rerun()
    
    st.sidebar.metric("⏳ Tempo", f"{t_rimanente // 60}:{t_rimanente % 60:02d}")
    
    q = st.session_state.df_filtrato.iloc[st.session_state.indice]
    st.markdown(f'<p class="quesito-style">Domanda {st.session_state.indice + 1}</p>', unsafe_allow_html=True)
    st.subheader(q['Domanda'])
    
    # Gestione Immagini
    if pd.notna(q.get('Immagine')):
        img_path = os.path.join("immagini", str(q['Immagine']).strip())
        if os.path.exists(img_path):
            st.image(img_path, width=400)

    opzioni = [str(q['A']), str(q['B']), str(q['C']), str(q['D'])]
    scelta = st.radio("Seleziona la risposta:", opzioni, index=None, key=f"q_{st.session_state.indice}")
    
    if scelta:
        mappa_risposte = {str(q['A']): 'A', str(q['B']): 'B', str(q['C']): 'C', str(q['D']): 'D'}
        st.session_state.risposte_date[st.session_state.indice] = mappa_risposte[scelta]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Precedente") and st.session_state.indice > 0:
            st.session_state.indice -= 1
            st.rerun()
    with col2:
        if st.session_state.indice < len(st.session_state.df_filtrato) - 1:
            if st.button("Successiva ➡️"):
                st.session_state.indice += 1
                st.rerun()
        else:
            if st.button("🏁 CONCLUDI TEST"):
                st.session_state.fase = "RISULTATI"
                st.rerun()

elif st.session_state.fase == "RISULTATI":
    esatte, errate, non_date, punti = calcola_risultati()
    st.balloons()
    st.markdown(f"""
        <div style="background:rgba(255,215,0,0.1); padding:20px; border-radius:15px; border:2px solid #FFD700; text-align:center;">
            <h2>Esito Test</h2>
            <h1>{punti} Punti</h1>
            <p>Esatte: {esatte} | Errate: {errate} | Non date: {non_date}</p>
        </div>
    """, unsafe_allow_html=True)
    
    pdf_data = genera_report_pdf()
    st.download_button("📥 Scarica Report PDF", pdf_data, "Report_AlPaTest.pdf", "application/pdf")
    
    if st.button("🔄 Ricomincia"):
        st.session_state.fase = "CONFIG"
        st.session_state.risposte_date = {}
        st.session_state.indice = 0
        st.rerun()
