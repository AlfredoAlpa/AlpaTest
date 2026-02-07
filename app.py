import streamlit as st
import os

# Configurazione
st.set_page_config(page_title="AlPaTest", layout="wide")

# LOGIN
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.title("🔐 Accesso AlPaTest")
    codice = st.text_input("Inserisci il codice:", type="password").strip()
    if st.button("Entra"):
        if codice in ["Open", "Studente01"]:
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Codice errato")
    st.stop()

# QUIZ
st.success("Benvenuto nel Quiz!")
st.title("📝 AlPaTest - Online")

# Qui puoi aggiungere le tue domande...
st.write("Il sistema è pronto. Carica le tue domande qui.")
