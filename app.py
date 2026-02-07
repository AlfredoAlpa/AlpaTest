import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# Configurazione pagina
st.set_page_config(page_title="AlPaTest - Concorso", layout="wide")

# Funzione per caricare le immagini in modo sicuro
def get_image_path(img_name):
    # Prova a cercare l'immagine nella cartella 'immagini' (minuscolo)
    path = os.path.join("immagini", img_name)
    if os.path.exists(path):
        return path
    return None

# --- LOGIN ---
if 'autenticato' not in st.session_state:
    st.session_state['autenticato'] = False

if not st.session_state['autenticato']:
    st.title("🔐 Accesso AlPaTest")
    codice = st.text_input("Inserisci il codice di accesso:", type="password")
    if st.button("Entra"):
        if codice == "1234": # Cambia il codice qui se vuoi
            st.session_state['autenticato'] = True
            st.rerun()
        else:
            st.error("Codice errato")
    st.stop()

# --- APP PRINCIPALE ---
st.title("📝 AlPaTest - Quiz Concorso")

# Esempio Domanda con Immagine
st.subheader("Domanda n. 15")
st.write("Osserva l'immagine seguente e rispondi:")

img_path = get_image_path("q15.jpg")
if img_path:
    st.image(img_path, width=400)
else:
    st.warning("Immagine q15.jpg non trovata nella cartella 'immagini'")

risposta = st.radio("Qual è la risposta corretta?", ["A", "B", "C", "D"], key="q15")

# --- GENERAZIONE REPORT PDF ---
if st.button("Genera Report Finale"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Titolo
    pdf.cell(190, 10, "Report Risultati Quiz", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    
    # Tabella Risultati - Larghezza 100% (circa 190mm per A4)
    # Ho impostato la larghezza a 190 per coprire tutto il foglio utile
    pdf.cell(95, 10, "Domanda", border=1)
    pdf.cell(95, 10, "Risposta Data", border=1, ln=True)
    
    pdf.cell(95, 10, "Domanda 15", border=1)
    pdf.cell(95, 10, risposta, border=1, ln=True)
    
    pdf_output = "report_finale.pdf"
    pdf.output(pdf_output)
    
    with open(pdf_output, "rb") as f:
        st.download_button("Scarica il Report PDF", f, file_name="Il_Tuo_Report.pdf")
