import streamlit as st
import pandas as pd
import os
import base64
import time
from fpdf import FPDF

# 1. CONFIGURAZIONE E LARGHEZZA UTILE
st.set_page_config(page_title="AIPaTest - CONCORSI", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewBlockContainer"] { padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    .stApp { background: linear-gradient(135deg, #1A3651 0%, #0D1B2A 100%); } 
    .logo-style { font-family: 'Georgia', serif; font-size: 3.2rem; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px #000; }
    .quesito-style { color: #FFEB3B !important; font-size: 1.7rem !important; font-weight: bold !important; }
    .timer-style { font-size: 2.7rem; font-weight: bold; text-align: right; color: #00FF00; }
    .nome-materia { font-size: 0.95rem !important; color: white !important; font-weight: 500; margin-bottom: 2px; }
    .report-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #FFD700; }
    hr { border-color: rgba(255,255,255,0.1); }
    .label-da-a { color: #FFD700; font-size: 13px !important; font-weight: bold; position: relative; z-index: 999; top: 10px; margin-bottom: 0px !important; }
    div[data-testid="stTextInput"] div[data-baseweb="input"] { min-height: 28px !important; height: 28px !important; background-color: black !important; }
    div[data-testid="stTextInput"] input { padding: 0px 10px !important; font-size: 0.85rem !important; height: 28px !important; }
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
    esatte, errate, non_date, punti_tot = calcola_risultati()
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
        pdf.set_font("helvetica", 'B', 11)
        pdf.multi_cell(0, 7, pulisci_testo(f"Domanda {i+1}: {row['Domanda']}"), border=0, align='L')
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, pulisci_testo(f"Tua Risposta: {r_u} | Risposta Esatta: {r_e}"), border=0, align='L')
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5) 
    return bytes(pdf.output())

# --- LOGIN ---
if not st.session_state.autenticato:
    st.markdown("""
        <div style="border: 3px solid #FFD700; border-radius: 20px; padding: 40px; background-color: rgba(0,0,0,0.6); text-align: center; max-width: 650px; margin: 40px auto;">
            <h1 style="color: #FFD700; font-size: 2.4rem;">🔐 Accesso AlPaTest</h1>
            <p style="color: white; font-size: 1.25rem;">Benvenuta/o. Inserisci il codice per iniziare.</p>
        </div>
    """, unsafe_allow_html=True)
    codice = st.text_input("Inserisci codice:", type="password", label_visibility="collapsed")
    if st.button("ENTRA"):
        df_codici_access = get_sheet_data("184205490")
        if not df_codici_access.empty and codice in df_codici_access.iloc[:,0].astype(str).values:
            st.session_state.autenticato = True
            st.rerun()
        else: st.error("Codice errato")
    st.stop()

# --- CARICAMENTO RISORSE ---
@st.cache_data
def carica_discipline():
    df_d = get_sheet_data("652955788") 
    if not df_d.empty:
        return pd.Series(df_d.Disciplina.values, index=df_d.Codice.astype(str)).to_dict()
    return {}

dict_discipline = carica_discipline()

@st.cache_data
def carica_codici_dispense():
    df_cod = get_sheet_data("170470777")
    if not df_cod.empty:
        return [str(x).strip().lower() for x in df_cod.iloc[:,0].dropna().tolist()]
    return []

codici_dispense = carica_codici_dispense()

def importa_quesiti():
    try:
        df = get_sheet_data("0")
        df.columns = ['Domanda','opz_A','opz_B','opz_C','opz_D','Corretta','Argomento','Immagine']
        df_p = get_sheet_data("614003066")
        if not df_p.empty:
            st.session_state.punteggi = {"Corretta": float(df_p.iloc[0,0]), "Non Data": float(df_p.iloc[0,1]), "Errata": float(df_p.iloc[0,2])}
        
        frames = []
        for i in range(9):
            d, a = st.session_state.get(f"da_{i}",""), st.session_state.get(f"a_{i}","")
            if d.strip().isdigit() and a.strip().isdigit():
                frames.append(df.iloc[int(d)-1 : int(a)])
        if frames:
            st.session_state.df_filtrato = pd.concat(frames).reset_index(drop=True)
            st.session_state.indice, st.session_state.risposte_date, st.session_state.start_time = 0, {}, time.time()
    except Exception as e: st.error(f"Errore: {e}")

@st.fragment(run_every=1)
def mostra_timer():
    if st.session_state.start_time and st.session_state.get("simulazione", False):
        rimanente = max(0, 1800 - (time.time() - st.session_state.start_time))
        st.markdown(f'<p class="timer-style">⏱️ {int(rimanente//60):02d}:{int(rimanente%60):02d}</p>', unsafe_allow_html=True)

# --- HEADER ---
t1, t2 = st.columns([7, 3])
with t1: st.markdown('<div class="logo-style">AlPaTest</div>', unsafe_allow_html=True)
with t2: mostra_timer()
st.markdown("<hr>", unsafe_allow_html=True)

# --- VISUALIZZAZIONE ---
if st.session_state.pdf_id_selezionato:
    if st.button("🔙 TORNA AI QUIZ", type="primary"): 
        st.session_state.pdf_id_selezionato = None
        st.rerun()
    url = f"https://drive.google.com/file/d/{st.session_state.pdf_id_selezionato}/preview"
    st.markdown(f'<iframe src="{url}" width="100%" height="950" style="border:none; background:white; border-radius:10px;"></iframe>', unsafe_allow_html=True)

elif st.session_state.fase == "FINE":
    es, er, nd, pt = calcola_risultati()
    st.markdown("## 📊 Risultato Finale")
    st.success(f"### Punteggio Totale: {pt}")
    c_pdf, c_new = st.columns(2)
    with c_pdf: st.download_button("📥 SCARICA REPORT PDF", genera_report_pdf(), "Report_AlPaTest.pdf", "application/pdf")
    with c_new:
        if st.button("🔄 NUOVA SIMULAZIONE", use_container_width=True): 
            st.session_state.clear(); st.rerun()
    st.write("---")
    for i, row in st.session_state.df_filtrato.iterrows():
        tua = st.session_state.risposte_date.get(i, "N.D.")
        corr = str(row['Corretta']).strip()
        colore = "#00FF00" if tua == corr else "#FF4B4B"
        st.markdown(f'<div class="report-card"><p style="color:{colore}; font-weight:bold;">Quesito {i+1}</p><p>{row["Domanda"]}</p><p>Tua: {tua} | Corr: {corr}</p></div>', unsafe_allow_html=True)

else:
    c_sx, c_ct, c_dx = st.columns([2.8, 7, 3.2])
    with c_sx:
        st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;padding:5px;border-radius:5px;">Navigazione</p>', unsafe_allow_html=True)
        if not st.session_state.df_filtrato.empty:
            with st.container(height=350):
                for i in range(len(st.session_state.df_filtrato)):
                    icona = "✅" if i in st.session_state.risposte_date else "⚪"
                    if st.button(f"{icona} Quesito {i+1}", key=f"nav_{i}", use_container_width=True):
                        st.session_state.indice = i; st.rerun()
        st.write("---")
        
        # --- SEZIONE DISPENSE AGGIORNATA ---
        with st.expander("📚 DISPENSE", expanded=True):
            if st.session_state.codice_dispense_valido == "":
                cod_s = st.text_input("Codice sblocco:", type="password")
                if cod_s.strip().lower() in codici_dispense:
                    st.session_state.codice_dispense_valido = cod_s.strip().lower()
                    st.rerun()
            
            if st.session_state.codice_dispense_valido != "":
                try:
                    # Carichiamo il foglio "Dispense" usando il GID 2095138066
                    df_disp = get_sheet_data("2095138066") 
                    if not df_disp.empty:
                        titoli = df_disp.iloc[:, 0].dropna().tolist()
                        sel = st.selectbox("Seleziona dispensa:", ["--"] + titoli)
                        if sel != "--" and st.button("📖 APRI DISPENSA"):
                            # Recupera l'ID Drive dalla Colonna B
                            st.session_state.pdf_id_selezionato = str(df_disp[df_disp.iloc[:,0] == sel].iloc[0, 1]).strip()
                            st.rerun()
                    else:
                        st.warning("Elenco dispense vuoto.")
                except:
                    st.warning("Errore caricamento dispense.")

    with c_ct:
        if not st.session_state.df_filtrato.empty:
            q = st.session_state.df_filtrato.iloc[st.session_state.indice]
            st.markdown(f'<div class="quesito-style">{st.session_state.indice+1}. {q["Domanda"]}</div>', unsafe_allow_html=True)
            if pd.notna(q.get('Immagine')) and str(q['Immagine']).strip() != "":
                nome_file = str(q['Immagine']).strip()
                percorso_img = os.path.join(os.path.dirname(__file__), "immagini", nome_file)
                if os.path.exists(percorso_img): st.image(percorso_img, width=450)
            
            opzioni = [f"A) {q['opz_A']}", f"B) {q['opz_B']}", f"C) {q['opz_C']}", f"D) {q['opz_D']}"]
            idx_sel = ["A","B","C","D"].index(st.session_state.risposte_date.get(st.session_state.indice)) if st.session_state.risposte_date.get(st.session_state.indice) else None
            scelta = st.radio("Risposta:", opzioni, index=idx_sel, key=f"rad_{st.session_state.indice}")
            if scelta: st.session_state.risposte_date[st.session_state.indice] = scelta[0]
            st.write("---")
            b1, b2, b3 = st.columns(3)
            if b1.button("⬅️ PREC.") and st.session_state.indice > 0: st.session_state.indice -= 1; st.rerun()
            if b2.button("🏁 CONSEGNA"): st.session_state.fase = "FINE"; st.rerun()
            if b3.button("SUCC. ➡️") and st.session_state.indice < len(st.session_state.df_filtrato)-1: st.session_state.indice += 1; st.rerun()
        else: st.info("Configura gli intervalli a destra e clicca su 'IMPORTA QUESITI'")

    with c_dx:
        st.markdown('<p style="background:#FFF;color:#000;text-align:center;font-weight:bold;padding:5px;border-radius:5px;">Configurazione</p>', unsafe_allow_html=True)
        for i in range(9):
            cod_mat = list(dict_discipline.keys())[i] if i < len(dict_discipline) else f"G{i+1}"
            nome_mat = dict_discipline.get(cod_mat, f"Gruppo {i+1}")
            st.markdown(f"<p class='nome-materia'>{cod_mat}: {nome_mat}</p>", unsafe_allow_html=True)
            c_d, c_a = st.columns(2)
            c_d.markdown('<p class="label-da-a">Da:</p>', unsafe_allow_html=True)
            c_d.text_input("da", key=f"da_{i}", label_visibility="collapsed")
            c_a.markdown('<p class="label-da-a">A:</p>', unsafe_allow_html=True)
            c_a.text_input("a", key=f"a_{i}", label_visibility="collapsed")
        st.write("---")
        st.checkbox("Simulazione (30 min)", key="simulazione")
        st.button("IMPORTA QUESITI", on_click=importa_quesiti, use_container_width=True)
