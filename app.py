import streamlit as st
import pandas as pd
import os
import time
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); } 
    .logo-style { font-family: 'Georgia', serif; font-size: 3rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; text-align: center; }
    .quesito-style { color: #FFEB3B !important; font-size: 2.2rem !important; font-weight: bold !important; line-height: 1.3; }
    .stRadio label p { font-size: 1.8rem !important; color: #FFFFFF !important; font-weight: 500 !important; }
    div[data-testid="stRadio"] > div { align-items: flex-start !important; color: white !important; }
    .timer-style { font-size: 2.5rem; font-weight: bold; text-align: right; }
    .stButton>button { height: 50px !important; font-weight: bold !important; }
    .risultato-box { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; color: white; border: 1px solid #FFD700; }
    </style>
    """, unsafe_allow_html=True)

# --- COSTANTI ---
SHEET_ID = "1JpsfojCbHrquUgP70pf7qD-KtIWN5iYCQeaRPh7dlJI"

# --- INIZIALIZZAZIONE STATO ---
if 'autenticato' not in st.session_state: st.session_state.autenticato = False
if 'fase' not in st.session_state: st.session_state.fase = "PROVA"
if 'df_filtrato' not in st.session_state: st.session_state.df_filtrato = pd.DataFrame()
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'punteggi' not in st.session_state: st.session_state.punteggi = {"Corretta": 0.75, "Non Data": 0.0, "Errata": -0.25}

# --- FUNZIONI TECNICHE ---
def pulisci_testo(testo):
    if pd.isna(testo) or testo == "": return " "
    repls = {'’':"'",'‘':"'",'“':'"','”':'"','–':'-','à':'a','è':'e','é':'e','ì':'i','ò':'o','ù':'u'}
    t = str(testo)
    for k,v in repls.items(): t = t.replace(k,v)
    return t.encode('latin-1','replace').decode('latin-1')

def calcola_risultati():
    corrette = 0
    sbagliate = 0
    senza_risposta = 0
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i)
        r_e = str(row['Corretta']).strip()
        if r_u is None: senza_risposta += 1
        elif r_u == r_e: corrette += 1
        else: sbagliate += 1
    punti = (corrette * st.session_state.punteggi["Corretta"]) + \
            (senza_risposta * st.session_state.punteggi["Non Data"]) + \
            (sbagliate * st.session_state.punteggi["Errata"])
    return corrette, sbagliate, senza_risposta, round(punti, 2)

def genera_report_pdf():
    corrette, sbagliate, senza_risposta, punti_tot = calcola_risultati()
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, pulisci_testo("REPORT FINALE - AlPaTest"), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(190, 8, pulisci_testo(f"PUNTEGGIO TOTALE: {punti_tot}"), ln=True, align='C')
    pdf.ln(10)
    for i, row in st.session_state.df_filtrato.iterrows():
        r_u = st.session_state.risposte_date.get(i, "N.D.")
        r_e = str(row['Corretta']).strip()
        pdf.set_font("helvetica", 'B', 11)
        pdf.multi_cell(190, 7, pulisci_testo(f"Domanda {i+1}: {row['Domanda']}"), border=0)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(190, 7, pulisci_testo(f"Tua Risposta: {r_u} | Risposta Esatta: {r_e}"), border=0)
        pdf.ln(5)
    return bytes(pdf.output())

def importa_quesiti():
    try:
        url_test = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Test"
        df = pd.read_csv(url_test).iloc[:, :8]
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        
        try:
            url_punteggi = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Punteggi"
            df_p = pd.read_csv(url_punteggi)
            st.session_state.punteggi = {"Corretta": float(df_p.iloc[0,0]), "Non Data": float(df_p.iloc[0,1]), "Errata": float(df_p.iloc[0,2])}
        except: pass

        frames = []
        for i in range(10):
            d, a = st.session_state.get(f"da_{i}",""), st.session_state.get(f"a_{i}","")
            if d.isdigit() and a.isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice = 0
            st.session_state.risposte_date = {}
            st.session_state.start_time = time.time()
            st.success("Dati caricati!")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- LOGICA ACCESSO ---
if not st.session_state.autenticato:
    st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("🔑 Inserisci Codice")
            cod_in = st.text_input("Codice di accesso", type="password", label_visibility="collapsed")
            if st.button("ACCEDI", use_container_width=True):
                try:
                    # Aggiunto un piccolo timeout e retry implicito
                    url_c = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Codici"
                    df_c = pd.read_csv(url_c, storage_options={'timeout': 10})
                    codici_validi = df_c.iloc[:, 0].astype(str).str.upper().tolist()
                    if cod_in.strip().upper() in codici_validi:
                        st.session_state.autenticato = True
                        st.rerun()
                    else:
                        st.error("Codice errato")
                except Exception as e:
                    st.error("Connessione in corso... Riprova tra un istante.")
    st.stop()

# --- INTERFACCIA PRINCIPALE ---
@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, (30 * 60) - (time.time() - st.session_state.start_time))
        m, s = int(rimanente // 60), int(rimanente % 60)
        st.markdown(f'<p class="timer-style" style="color:{"#00FF00" if rimanente > 300 else "#FF0000"}">⏱️ {m:02d}:{s:02d}</p>', unsafe_allow_html=True)
        if rimanente <= 0:
            st.session_state.fase = "CONCLUSIONE"
            st.rerun()

if st.session_state.fase in ["CONFERMA", "CONCLUSIONE"]:
    st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
    if st.session_state.fase == "CONFERMA":
        with st.container(border=True):
            st.write("## ❓ Vuoi consegnare?")
            c1, c2 = st.columns(2)
            if c1.button("Sì, CONSEGNA", use_container_width=True):
                st.session_state.fase = "CONCLUSIONE"; st.rerun()
            if c2.button("No, CONTINUA", use_container_width=True):
                st.session_state.fase = "PROVA"; st.rerun()
    else:
        cor, sba, nnd, pti = calcola_risultati()
        st.markdown(f'<div class="risultato-box"><h2>✅ Esame completato!</h2><p>Punteggio: <b>{pti}</b></p></div>', unsafe_allow_html=True)
        st.download_button("📩 SCARICA REPORT E ESCI", data=genera_report_pdf(), file_name="esito.pdf", on_click=lambda: st.session_state.clear())
    st.stop()

t1, t2 = st.columns([7, 3])
with t1: st.markdown('<div class="logo-style" style="text-align:left;">AlPaTest</div>', unsafe_allow_html=True)
with t2: mostra_timer()
st.markdown("<hr>", unsafe_allow_html=True)

col_sx, col_centro, col_dx = st.columns([2.8, 7, 3.2])
with col_sx:
    if not st.session_state.df_filtrato.empty:
        with st.container(height=500):
            lista = [f"{'✓' if i in st.session_state.risposte_date else '  '} Quesito {i+1}" for i in range(len(st.session_state.df_filtrato))]
            sel = st.radio("Domande", lista, index=st.session_state.indice, label_visibility="collapsed", key=f"nav_{st.session_state.indice}")
            st.session_state.indice = lista.index(sel)

with col_centro:
    if not st.session_state.df_filtrato.empty:
        q = st.session_state.df_filtrato.iloc[st.session_state.indice]
        st.markdown(f'<div class="quesito-style">{st.session_state.indice + 1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
        if pd.notna(q['Immagine']) and str(q['Immagine']).strip():
            p_img = os.path.join("immagini", str(q['Immagine']))
            if os.path.exists(p_img): st.image(p_img, use_container_width=True)
        
        opts = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
        ans_prec = st.session_state.risposte_date.get(st.session_state.indice)
        idx_prec = ["A","B","C","D"].index(ans_prec) if ans_prec in ["A","B","C","D"] else None
        
        def salva(): st.session_state.risposte_date[st.session_state.indice] = st.session_state[f"r_{st.session_state.indice}"][0]
        st.radio("R", opts, key=f"r_{st.session_state.indice}", index=idx_prec, on_change=salva, label_visibility="collapsed")
    else: st.info("Configura i gruppi a destra e clicca Importa")

with col_dx:
    st.checkbox("Simulazione (30 min)", key="simulazione")
    for i in range(10):
        r1, r2 = st.columns(2)
        r1.text_input("D", key=f"da_{i}", placeholder="Da", label_visibility="collapsed")
        r2.text_input("A", key=f"a_{i}", placeholder="A", label_visibility="collapsed")
    st.button("Importa Quesiti", on_click=importa_quesiti, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
n1, n2, n3, _ = st.columns([1.5, 1.5, 1.5, 5.5])
if n1.button("⏮️ Precedente"):
    if st.session_state.indice > 0: st.session_state.indice -= 1; st.rerun()
if n2.button("🏆 CONSEGNA"):
    if not st.session_state.df_filtrato.empty: st.session_state.fase = "CONFERMA"; st.rerun()
if n3.button("Successivo ⏭️"):
    if st.session_state.indice < len(st.session_state.df_filtrato) - 1: st.session_state.indice += 1; st.rerun()