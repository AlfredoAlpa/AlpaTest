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
            background-color: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            border: 2px solid #FFD700;
            max-width: 500px;
            margin: 50px auto;
            text-align: center;
        }
        div[data-testid="stTextInput"] input {
            height: 90px !important;
            font-size: 2.2rem !important;
            text-align: center !important;
            border: 2px solid #FFD700 !important;
            background-color: white !important;
            color: black !important;
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
    st.markdown('<p style="color:#FFD700; font-size:1.4rem;">Codice di accesso:</p>', unsafe_allow_html=True)
    codice = st.text_input("Codice", type="password", key="pwd_box").strip()
    if st.button("Entra"):
        if codice.lower() in ["open", "studente01"]:
            st.session_state.autenticato = True
            st.rerun()
        else:
            st.error("Codice errato")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 3. CSS GENERALE
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); }
    .logo-style { font-family: 'Georgia', serif; font-size: 3.5rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.6rem !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. INIZIALIZZAZIONE
if 'fase' not in st.session_state: st.session_state.fase = "CONFIG"
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'indice' not in st.session_state: st.session_state.indice = 0

# 5. FUNZIONI PDF (LARGHEZZA 100)
def pulisci_testo(testo):
    return str(testo).encode('latin-1', 'replace').decode('latin-1')

def calcola_risultati():
    esatte, errate, non_date = 0, 0, 0
    if 'df_filtrato' in st.session_state:
        # Nota: usiamo 'corretta' con la minuscola come indicato dal tuo errore
        for i, row in st.session_state.df_filtrato.iterrows():
            r_u = st.session_state.risposte_date.get(i)
            r_e = str(row['corretta']).strip()
            if r_u is None: non_date += 1
            elif r_u == r_e: esatte += 1
            else: errate += 1
    punti = (esatte * 0.75) + (errate * -0.25)
    return esatte, errate, non_date, round(punti, 2)

def genera_report_pdf():
    esatte, errate, non_date, punti = calcola_risultati()
    pdf = FPDF()
    pdf.add_page()
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
        pdf.cell(larghezza_utile, 6, pulisci_testo(f"Tua: {r_u} | Corretta: {row['corretta']}"), ln=True)
        pdf.ln(2)
    return bytes(pdf.output())

# 6. LOGICA PRINCIPALE (MODIFICATA PER IL TUO EXCEL)
st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
st.write("---")

if st.session_state.fase == "CONFIG":
    if os.path.exists("quiz.xlsx"):
        # LEGGIAMO IL FOGLIO "quiz"
        df = pd.read_excel("quiz.xlsx", sheet_name="quiz")
        df.columns = [str(c).strip() for c in df.columns]
        
        # USIAMO "Argomento" INVECE DI "Materia"
        if 'Argomento' in df.columns:
            materie = df['Argomento'].unique().tolist()
            with st.sidebar:
                st.title("⚙️ Impostazioni")
                materia_scelta = st.selectbox("Scegli Materia/Argomento", materie)
                n_domande = st.number_input("Numero Domande", 5, 100, 20)
                tempo_min = st.slider("Minuti", 1, 60, 10)
                if st.button("🚀 INIZIA TEST"):
                    st.session_state.df_filtrato = df[df['Argomento'] == materia_scelta].sample(n_domande).reset_index(drop=True)
                    st.session_state.fase = "QUIZ"
                    st.session_state.fine_test = time.time() + (tempo_min * 60)
                    st.rerun()
        else:
            st.error(f"Colonna 'Argomento' non trovata. Colonne presenti: {list(df.columns)}")
    else:
        st.error("File 'quiz.xlsx' non trovato su GitHub!")

elif st.session_state.fase == "QUIZ":
    t_rimanente = int(st.session_state.fine_test - time.time())
    if t_rimanente <= 0:
        st.session_state.fase = "RISULTATI"
        st.rerun()
    
    st.sidebar.metric("⏳ Tempo", f"{t_rimanente // 60}:{t_rimanente % 60:02d}")
    q = st.session_state.df_filtrato.iloc[st.session_state.indice]
    st.markdown(f'<p class="quesito-style">Domanda {st.session_state.indice + 1}</p>', unsafe_allow_html=True)
    st.subheader(q['Domanda'])
    
    if 'Immagine' in q and pd.notna(q['Immagine']):
        img_path = os.path.join("immagini", str(q['Immagine']).strip())
        if os.path.exists(img_path):
            st.image(img_path, width=400)

    opzioni = [str(q['A']), str(q['B']), str(q['C']), str(q['D'])]
    scelta = st.radio("Seleziona la risposta:", opzioni, index=None, key=f"q_{st.session_state.indice}")
    if scelta:
        mappa = {str(q['A']):'A', str(q['B']):'B', str(q['C']):'C', str(q['D']):'D'}
        st.session_state.risposte_date[st.session_state.indice] = mappa[scelta]

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
    st.success(f"Test Completato! Punteggio: {punti}")
    pdf_data = genera_report_pdf()
    st.download_button("📥 Scarica Report PDF", pdf_data, "Report_AlPaTest.pdf", "application/pdf")
    if st.button("🔄 Ricomincia"):
        st.session_state.fase = "CONFIG"
        st.session_state.risposte_date = {}
        st.session_state.indice = 0
        st.rerun()
