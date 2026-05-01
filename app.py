import streamlit as st
import pandas as pd
import random
import os

# Konfiguracja VIP
st.set_page_config(page_title="Chleb-App VIP", page_icon="🥖")

# ZMIENIŁEM NAZWĘ PLIKU, ABY SAMO DODRABIAŁO NOWE KOLUMNY
DB_FILE = "baza_v4_nagrody.csv"

# Funkcja ładowania danych (obsługuje teraz nagrody)
def load_data():
    kolumny = ['Nazwa', 'Gmail', 'Haslo', 'Kod', 'Punkty', 'Aktywna_Nagroda']
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype={'Kod': str, 'Haslo': str, 'Aktywna_Nagroda': str})
        for col in kolumny:
            if col not in df.columns:
                df[col] = "" if col == 'Aktywna_Nagroda' else (0 if col == 'Punkty' else "")
        return df[kolumny]
    return pd.DataFrame(columns=kolumny)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

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
                    if str(user_row.iloc[0]['Haslo']) == str(login_pass):
                        st.session_state.logged_in_email = login_email
                        st.query_params["user_email"] = login_email
                        st.rerun()
                    else:
                        st.error("Błędne hasło!")
                else:
                    st.error("Nie znaleziono konta.")
        
        with tab2:
            st.subheader("Załóż nowe konto")
            st.warning("⚠️ NIE wpisuj tu swojego prawdziwego hasła do Gmaila!")
            new_name = st.text_input("Twoje Imię:")
            new_email = st.text_input("Twój Gmail:")
            new_pass = st.text_input("Hasło do apki:", type="password")
            
            if st.button("Zarejestruj mnie (+5 pkt!)"):
                if new_name and new_email and new_pass:
                    if new_email not in st.session_state.db['Gmail'].values:
                        nowy_kod = str(random.randint(10000, 99999))
                        nowy_user = pd.DataFrame([{
                            'Nazwa': new_name, 'Gmail': new_email, 'Haslo': str(new_pass), 
                            'Kod': nowy_kod, 'Punkty': 5, 'Aktywna_Nagroda': ""
                        }])
                        st.session_state.db = pd.concat([st.session_state.db, nowy_user], ignore_index=True)
                        save_data(st.session_state.db)
                        st.session_state.logged_in_email = new_email
                        st.query_params["user_email"] = new_email
                        st.success("Konto założone!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Ten Gmail jest już zajęty.")

    else:
        user_row = st.session_state.db[st.session_state.db['Gmail'] == st.session_state.logged_in_email]
        if not user_row.empty:
            idx = user_row.index[0]
            name = user_row.iloc[0]['Nazwa']
            kod = user_row.iloc[0]['Kod']
            pkt = user_row.iloc[0]['Punkty']
            aktywna = user_row.iloc[0]['Aktywna_Nagroda']
            
            st.header(f"Witaj, {name}!")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Twoje Zapasy", f"{pkt} Bąbelków")
            with col_b:
                st.metric("Twój Kod", kod)
            
            # Stan aktywacji kuponu
            if pd.isna(aktywna) or aktywna == "":
                st.write("---")
                st.subheader("🎁 Aktywuj nagrodę za punkty:")
                
                cennik = {"Mini Pizza": 30, "Zakwas": 50, "Chleb": 70}
                
                for nagroda, koszt in cennik.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{nagroda}** ({koszt} Bąbelków)")
                    with col2:
                        if st.button("Aktywuj", key=nagroda):
                            if pkt >= koszt:
                                st.session_state.db.loc[idx, 'Punkty'] -= koszt
                                st.session_state.db.loc[idx, 'Aktywna_Nagroda'] = nagroda
                                save_data(st.session_state.db)
                                st.success(f"Aktywowano: {nagroda}!")
                                st.rerun()
                            else:
                                st.error("Za mało punktów!")
            else:
                st.warning(f"🎫 MASZ AKTYWNY KUPON NA: **{aktywna}**")
                st.info("Pokaż swój kod 5-cyfrowy przy stoisku, aby odebrać nagrodę!")
            
            st.write("---")
            if st.button("Wyloguj"):
                st.session_state.logged_in_email = None
                st.query_params.clear()
                st.rerun()

elif menu == "Panel Sprzedawcy":
    st.header("Panel Admina")
    pin = st.text_input("Hasło VIP:", type="password")
    if pin == "milosz2137":
        kod_input = st.text_input("Wpisz 5-cyfrowy kod klienta:")
        
        if kod_input:
            user_search = st.session_state.db[st.session_state.db['Kod'] == kod_input]
            if not user_search.empty:
                idx = user_search.index[0]
                klient = user_search.iloc[0]['Nazwa']
                punkty_klienta = user_search.iloc[0]['Punkty']
                kupon = user_search.iloc[0]['Aktywna_Nagroda']
                
                st.write(f"**Klient:** {klient} | **Punkty:** {punkty_klienta}")
                
                # WYŚWIETLANIE AKTYWNEGO KUPONU
                if kupon and kupon != "":
                    st.warning(f"🔔 Klient chce odebrać: **{kupon}**")
                    if st.button("Wydaj nagrodę (Kasuje kupon)"):
                        st.session_state.db.loc[idx, 'Aktywna_Nagroda'] = ""
                        save_data(st.session_state.db)
                        st.success("Wydano nagrodę!")
                        st.rerun()
                else:
                    st.info("Klient nie ma aktywowanych nagród.")
                
                st.write("---")
                ile_pkt = st.number_input("Dodaj punkty za zakupy:", value=10)
                if st.button("DODAJ PUNKTY"):
                    st.session_state.db.loc[idx, 'Punkty'] += ile_pkt
                    save_data(st.session_state.db)
                    st.success(f"Dodano! Klient ma teraz {st.session_state.db.loc[idx, 'Punkty']} pkt.")
                    st.rerun()
            else:
                st.error("Nie znaleziono kodu.")
        
        st.subheader("Baza Klientów")
        st.dataframe(st.session_state.db)

elif menu == "YouTube & Info":
    st.header("Subskrybuj Inżynier Wypieku!")
    st.link_button("🔴 WEJDŹ NA MÓJ KANAŁ YT", "https://www.youtube.com/@inzynierwypieku")



