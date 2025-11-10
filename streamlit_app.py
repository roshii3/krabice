import streamlit as st
from supabase import create_client
from datetime import datetime

# ---------- CONFIG ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

# ---------- STYLING ----------
st.markdown("""
<style>
.big-button button {height:60px; font-size:26px; background-color:#4CAF50; color:white; width:100%; margin-top:10px;}
.big-input input {height:55px; font-size:22px; margin-bottom:10px;}
.radio-horizontal .stRadio > label {font-size:22px;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "kontrolor" not in st.session_state:
    st.session_state.kontrolor = ""
if "form_visible" not in st.session_state:
    st.session_state.form_visible = True
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# ---------- LOGIN ----------
if not st.session_state.kontrolor:
    st.session_state.kontrolor = st.text_input("Zadajte meno kontrolóra:")

if st.session_state.kontrolor:
    st.info(f"Aktuálne prihlásený kontrolór: {st.session_state.kontrolor}")
    if st.button("Odhlásiť kontrolóra"):
        st.session_state.kontrolor = ""
        st.rerun()

st.write("---")

# ---------- FORM ----------
def vykresli_formular():
    key = f"form_{st.session_state.form_key}"
    
    # Číslo palety
      #paleta_id = st.text_input("Číslo palety:", key=f"{key}_paleta_id")
    # Číslo palety – vhodné pre čiarový kód
    paleta_id = st.text_input(
    "Naskenujte čiarový kód palety:",
    key=f"{key}_paleta_id",
    placeholder="Naskenujte paletu cez skener..."
    )
    # 1️⃣ SPÔSOB ZADANIA
    zadanie_typ = st.radio(
        "Ako chce kontrolór zadať počet?",
        ("Manuálne", "Výpočet podľa vrstiev"),
        key=f"{key}_zadanie",
        horizontal=True
    )
    
    # 2️⃣ BD INFORMÁCIA (vždy)
    bd_balenie = st.radio("Ide o BD balenie?", ("Áno", "Nie"), key=f"{key}_bd", horizontal=True)
    bd = True if bd_balenie == "Áno" else False
    typ_bd = st.text_input("Typ BD (napr. BD4, BD6):", key=f"{key}_typ_bd") if bd else None

    # 3️⃣ Zadanie počtu
    manual_count = None
    celkovy_pocet_jednotiek = None
    pocet_v_rade = pocet_radov = pocet_volnych = None

    if zadanie_typ == "Manuálne":
        manual_count = st.number_input("Zadajte počet jednotiek (manuálne):", min_value=0, step=1, key=f"{key}_manual")
    else:
        pocet_v_rade = st.number_input("Počet krabíc v rade:", min_value=1, step=1, key=f"{key}_v_rade")
        pocet_radov = st.number_input("Počet radov na palete:", min_value=1, step=1, key=f"{key}_radov")
        pocet_volnych = st.number_input("Počet voľných krabíc navrchu:", min_value=0, step=1, key=f"{key}_volne")

        pocet_krabic = pocet_v_rade * pocet_radov + pocet_volnych
        celkovy_pocet_jednotiek = pocet_krabic

        if bd and typ_bd:
            try:
                celkovy_pocet_jednotiek *= int(typ_bd.replace("BD", ""))
            except:
                st.warning("Nepodarilo sa rozpoznať typ BD, použité 1x")

    # 4️⃣ ULOŽENIE
    if st.button("💾 Uložiť", key=f"{key}_ulozit", use_container_width=True):
        if not paleta_id:
            st.error("Zadajte číslo palety!")
            return

        data = {
            "paleta_id": paleta_id,
            "bd": bd,
            "typ_bd": typ_bd,
            "pocet_v_rade": pocet_v_rade,
            "pocet_radov": pocet_radov,
            "pocet_volnych": pocet_volnych,
            "celkovy_pocet_jednotiek": celkovy_pocet_jednotiek,
            "manual_count": manual_count,
            "kontrolor": st.session_state.kontrolor,
            "datum": datetime.now().isoformat()
        }

        try:
            databaze.table("palety").insert(data).execute()

            # Log
            databaze.table("palety_log").insert({
                "paleta_id": paleta_id,
                "akcia": f"Paleta {paleta_id} vytvorená ({'BD' if bd else 'non-BD'}, {zadanie_typ.lower()})",
                "kontrolor": st.session_state.kontrolor,
                "datum": datetime.now().isoformat()
            }).execute()

            st.success(f"Paleta {paleta_id} úspešne uložená ✅")
            st.session_state.form_visible = False
            st.rerun()

        except Exception as e:
            st.error("⚠️ Chyba pri ukladaní do databázy.")
            st.write(e)

# ---------- FORM LOGIKA ----------
if st.session_state.form_visible:
    vykresli_formular()
else:
    st.button("➕ Nová paleta", on_click=lambda: (
        st.session_state.update(form_visible=True, form_key=st.session_state.form_key + 1)
    ), use_container_width=True)
