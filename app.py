import streamlit as st
import pandas as pd
import random
import os

# Konfiguracja VIP
st.set_page_config(page_title="Chleb-App VIP", page_icon="🥖")

DB_FILE = "baza_zapasow.csv"

# Funkcja ładowania danych
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={'Kod': str})
    return pd.DataFrame(columns=['Nazwa', 'Kod', 'Punkty'])

# Funkcja zapisu danych
def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Inicjalizacja bazy w sesji
if 'db' not in st.session_state:
    st.session_state.db = load_data()

# --- LOGIKA AUTOMATYCZNEGO LOGOWANIA ---
# Pobieramy imię z adresu URL (jeśli istnieje)
if "user" in st.query_params:
    st.session_state.logged_in_user = st.query_params["user"]
elif "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# INTERFEJS
st.title("🥖 Chleb-App VIP")
menu = st.sidebar.radio("Menu", ["Mój Profil", "Panel Sprzedawcy", "YouTube & Info"])

if menu == "Mój Profil":
    # Jeśli użytkownik nie jest zalogowany
    if st.session_state.logged_in_user is None:
        st.header("Zaloguj się lub zarejestruj")
        name_input = st.text_input("Podaj swoje imię:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Sprawdź moje punkty"):
                if name_input:
                    user_row = st.session_state.db[st.session_state.db['Nazwa'] == name_input]
                    if not user_row.empty:
                        st.session_state.logged_in_user = name_input
                        st.query_params["user"] = name_input # Zapamiętuje w linku
                        st.rerun()
                    else:
                        st.error("Nie znaleziono takiego imienia.")
                else:
                    st.warning("Wpisz imię!")
        
        with col2:
            if st.button("Nowe konto (+5 pkt)"):
                if name_input:
                    if name_input not in st.session_state.db['Nazwa'].values:
                        nowy_kod = str(random.randint(10000, 99999))
                        nowy_user = pd.DataFrame([{'Nazwa': name_input, 'Kod': nowy_kod, 'Punkty': 5}])
                        st.session_state.db = pd.concat([st.session_state.db, nowy_user], ignore_index=True)
                        save_data(st.session_state.db)
                        st.session_state.logged_in_user = name_input
                        st.query_params["user"] = name_input # Zapamiętuje w linku
                        st.success("Witaj w klubie!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("To imię jest już zajęte.")
                else:
                    st.warning("Wpisz imię!")

    # Jeśli użytkownik JEST już zalogowany
    else:
        user_row = st.session_state.db[st.session_state.db['Nazwa'] == st.session_state.logged_in_user]
        if not user_row.empty:
            name = st.session_state.logged_in_user
            kod = user_row.iloc[0]['Kod']
            pkt = user_row.iloc[0]['Punkty']
            
            st.header(f"Witaj, {name}!")
            st.metric("Twoje Zapasy", f"{pkt} Bąbelków")
            st.subheader(f"Twój Kod: {kod}")
            st.info("Pokaż ten kod przy stoisku, aby dostać punkty!")
            
            if st.button("Wyloguj (Zmień konto)"):
                st.session_state.logged_in_user = None
                st.query_params.clear() # Czyści link
                st.rerun()

elif menu == "Panel Sprzedawcy":
    st.header("Panel Admina")
    pin = st.text_input("Hasło VIP:", type="password")
    if pin == "milosz2137": # Twoje hasło
        kod_input = st.text_input("Wpisz 5-cyfrowy kod klienta:")
        ile_pkt = st.number_input("Ile punktów dodać?", value=10)
        
        if st.button("DODAJ PUNKTY"):
            if kod_input in st.session_state.db['Kod'].values:
                st.session_state.db.loc[st.session_state.db['Kod'] == kod_input, 'Punkty'] += ile_pkt
                save_data(st.session_state.db)
                user_name = st.session_state.db.loc[st.session_state.db['Kod'] == kod_input, 'Nazwa'].values[0]
                st.success(f"Dodano! {user_name} ma teraz {st.session_state.db.loc[st.session_state.db['Kod'] == kod_input, 'Punkty'].values[0]} pkt.")
            else:
                st.error("Błędny kod!")
        
        st.subheader("Baza Klientów")
        st.dataframe(st.session_state.db)

elif menu == "YouTube & Info":
    st.header("Subskrybuj Inżynier Wypieku!")
    
    # GŁÓWNY PRZYCISK DO KANAŁU
    st.link_button("🔴 WEJDŹ NA MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")
    
    st.write("---")
    st.subheader("Jak upiec idealny chleb?")
    st.write("Oglądaj moje poradniki, aby Twój zakwas zawsze był silny!")

