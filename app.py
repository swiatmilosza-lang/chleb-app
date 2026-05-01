import streamlit as st
import pandas as pd
import random
import os

# Konfiguracja VIP
st.set_page_config(page_title="Chleb-App VIP", page_icon="🥖")

DB_FILE = "baza_zapasow.csv"

# Funkcja ładowania danych (dodaliśmy kolumny Gmail i Haslo)
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={'Kod': str, 'Haslo': str})
    return pd.DataFrame(columns=['Nazwa', 'Gmail', 'Haslo', 'Kod', 'Punkty'])

# Funkcja zapisu danych
def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Inicjalizacja bazy w sesji
if 'db' not in st.session_state:
    st.session_state.db = load_data()

# LOGIKA AUTOMATYCZNEGO LOGOWANIA
if "user_email" in st.query_params:
    st.session_state.logged_in_email = st.query_params["user_email"]
elif "logged_in_email" not in st.session_state:
    st.session_state.logged_in_email = None

# INTERFEJS
st.title("🥖 Chleb-App VIP")
menu = st.sidebar.radio("Menu", ["Mój Profil", "Panel Sprzedawcy", "YouTube & Info"])

if menu == "Mój Profil":
    # Jeśli użytkownik NIE JEST zalogowany
    if st.session_state.logged_in_email is None:
        st.header("Zaloguj się lub załóż konto")
        
        tab1, tab2 = st.tabs(["Logowanie", "Rejestracja"])
        
        with tab1:
            st.subheader("Zaloguj się")
            login_email = st.text_input("Twój Gmail:", key="login_email")
            login_pass = st.text_input("Hasło:", type="password", key="login_pass")
            
            if st.button("Zaloguj się"):
                user_row = st.session_state.db[st.session_state.db['Gmail'] == login_email]
                if not user_row.empty:
                    # Sprawdzamy czy hasło się zgadza
                    if str(user_row.iloc[0]['Haslo']) == str(login_pass):
                        st.session_state.logged_in_email = login_email
                        st.query_params["user_email"] = login_email
                        st.rerun()
                    else:
                        st.error("Błędne hasło!")
                else:
                    st.error("Nie znaleziono konta z tym adresem Gmail.")
        
        with tab2:
            st.subheader("Załóż nowe konto")
            st.warning("⚠️ Twórz unikalne hasło! NIE wpisuj tu swojego prawdziwego hasła do Gmaila!")
            new_name = st.text_input("Twoje Imię:")
            new_email = st.text_input("Twój Gmail:")
            new_pass = st.text_input("Wymyśl hasło do apki:", type="password")
            
            if st.button("Zarejestruj mnie (+5 pkt!)"):
                if new_name and new_email and new_pass:
                    # Sprawdzamy czy email już istnieje
                    if new_email not in st.session_state.db['Gmail'].values:
                        nowy_kod = str(random.randint(10000, 99999))
                        nowy_user = pd.DataFrame([{
                            'Nazwa': new_name, 
                            'Gmail': new_email, 
                            'Haslo': str(new_pass), 
                            'Kod': nowy_kod, 
                            'Punkty': 5
                        }])
                        st.session_state.db = pd.concat([st.session_state.db, nowy_user], ignore_index=True)
                        save_data(st.session_state.db)
                        
                        st.session_state.logged_in_email = new_email
                        st.query_params["user_email"] = new_email
                        st.success("Konto założone pomyślnie!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Ten adres Gmail jest już zarejestrowany.")
                else:
                    st.warning("Wypełnij wszystkie pola!")

    # Jeśli użytkownik JEST zalogowany
    else:
        user_row = st.session_state.db[st.session_state.db['Gmail'] == st.session_state.logged_in_email]
        if not user_row.empty:
            name = user_row.iloc[0]['Nazwa']
            kod = user_row.iloc[0]['Kod']
            pkt = user_row.iloc[0]['Punkty']
            
            st.header(f"Witaj, {name}!")
            st.metric("Twoje Zapasy", f"{pkt} Bąbelków")
            st.subheader(f"Twój Kod: {kod}")
            st.info("Pokaż ten kod przy stoisku, aby dostać punkty!")
            
            if st.button("Wyloguj (Zmień konto)"):
                st.session_state.logged_in_email = None
                st.query_params.clear()
                st.rerun()

elif menu == "Panel Sprzedawcy":
    st.header("Panel Admina")
    pin = st.text_input("Hasło VIP:", type="password")
    if pin == "milosz2137": # Twoje hasło admina
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
    st.header("Subskrybuj światmilosza-lang!")
    st.link_button("🔴 WEJDŹ NA MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")


