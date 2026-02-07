import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="AlPaTest - Quiz Online", layout="wide")

# Funzione per gestire le immagini in modo sicuro
def mostra_immagine(nome_file):
    percorso = os.path.join("immagini", nome_file)
    if os.path.exists(percorso):
        st.image(percorso, width=600)
    else:
        st.warning(f"⚠️ Immagine '{nome_file}' non trovata nella cartella 'immagini'.")

# --- 2. LOGIN ---
if 'autenticato' not in st.session_state:
    st.session_state['autenticato'] = False

if not st.session_state['autenticato']:
    st.title("🔐 Accesso AlPaTest")
    # Il codice viene convertito in minuscolo per evitare errori di maiuscole
    codice_input = st.text_input("Inserisci codice (Open o Studente01):", type="password").strip().lower()
    
    if st.button("Accedi"):
        if codice_input in ["open", "studente01"]:
            st.session_state['autenticato'] = True
            st.rerun()
        else:
            st.error("Codice errato. Riprova.")
    st.stop()

# --- 3. QUIZ (Appare solo dopo il Login) ---
st.title("📝 AlPaTest - Sessione Quiz")
st.write("Rispondi a tutte le domande e clicca sul tasto in fondo per il report.")

# Dizionario per salvare le risposte
risposte_utente = {}

# --- ESEMPIO DOMANDA 15 (Con immagine) ---
st.markdown("---")
st.subheader("Domanda n. 15")
st.write("Analizza l'immagine e seleziona l'opzione corretta:")
mostra_immagine("q15.jpg")
risposte_utente["Domanda 15"] = st.radio("Tua risposta:", ["A", "B", "C", "D"], key="q15")

# --- ESEMPIO ALTRE DOMANDE (Puoi duplicare questo blocco) ---
st.markdown("---")
st.subheader("Domanda n. 16")
st.write("Qual è il valore della variabile X nel grafico?")
# mostra_immagine("q16.jpg") # Decommenta se hai l'immagine
risposte_utente["Domanda 16"] = st.radio("Tua risposta:", ["A", "B", "C", "D"], key="q16")


# --- 4. GENERAZIONE REPORT PDF (Larghezza 100%) ---
st.markdown("---")
if st.button("🏁 Termina Quiz e Genera Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Titolo
    pdf.cell(190, 10, "Report Risultati AlPaTest", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    # Intestazione Tabella
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(95, 10, "Domanda", border=1, fill=True)
    pdf.cell(95, 10, "Risposta Data", border=1, fill=True, ln=True)
    
    # Ciclo per inserire tutte le risposte date
    for domanda, risp in risposte_utente.items():
        pdf.cell(95, 10, domanda, border=1)
        pdf.cell(95, 10, risp, border=1, ln=True)
    
    # Salvataggio
    pdf_file = "Report_AlPaTest.pdf"
    pdf.output(pdf_file)
    
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📥 Scarica Report PDF",
            data=f,
            file_name="Risultati_Quiz.pdf",
            mime="application/pdf"
        )
    st.balloons()
