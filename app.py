import streamlit as st
import pandas as pd
import random
import os

# Konfiguracja VIP
st.set_page_config(page_title="Chleb-App VIP", page_icon="🥖")

DB_FILE = "baza_zapasow.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={'Kod': str})
    return pd.DataFrame(columns=['Nazwa', 'Kod', 'Punkty'])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if 'db' not in st.session_state:
    st.session_state.db = load_data()

# INTERFEJS
st.title("🥖 Chleb-App VIP")
menu = st.sidebar.radio("Menu", ["Mój Profil (Klient)", "Panel Sprzedawcy", "YouTube & Info"])

if menu == "Mój Profil (Klient)":
    st.header("Twoje Zapasy")
    name = st.text_input("Podaj imię, by sprawdzić punkty:")
    if name:
        user_row = st.session_state.db[st.session_state.db['Nazwa'] == name]
        if not user_row.empty:
            kod = user_row.iloc[0]['Kod']
            pkt = user_row.iloc[0]['Punkty']
            st.metric("Twoje Punkty", f"{pkt} Zapasów")
            st.code(f"TWÓJ KOD: {kod}", language=None)
            st.info("Pokaż ten kod przy stoisku!")
        else:
            if st.button("Zarejestruj mnie i daj 5 pkt na start!"):
                nowy_kod = str(random.randint(10000, 99999))
                nowy_user = pd.DataFrame([{'Nazwa': name, 'Kod': nowy_kod, 'Punkty': 5}])
                st.session_state.db = pd.concat([st.session_state.db, nowy_user], ignore_index=True)
                save_data(st.session_state.db)
                st.success(f"Witaj w klubie! Twój kod to: {nowy_kod}")
                st.balloons()

elif menu == "Panel Sprzedawcy":
    st.header("Panel Admina")
    pin = st.text_input("Hasło VIP:", type="password")
    if pin == "miłosz2137": # Tu ustaw swoje hasło
        kod_input = st.text_input("Wpisz kod klienta:")
        ile_pkt = st.number_input("Punkty za zakup:", value=10)
        if st.button("Dodaj Punkty"):
            if kod_input in st.session_state.db['Kod'].values:
                st.session_state.db.loc[st.session_state.db['Kod'] == kod_input, 'Punkty'] += ile_pkt
                save_data(st.session_state.db)
                st.success("Dodano!")
            else:
                st.error("Błędny kod!")
        st.dataframe(st.session_state.db)

elif menu == "YouTube & Info":
    st.header("Subskrybuj kanał!")
    st.video("TU_WKLEJ_LINK_DO_FILMU")
    st.write("Dzięki aplikacji masz dostęp do tajnych przepisów!")
