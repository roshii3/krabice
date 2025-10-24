import streamlit as st
from supabase import create_client
from datetime import datetime

# ---------- CONFIG ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

st.set_page_config(page_title="Palety", page_icon="📦", layout="centered")

# ---------- STYLING ----------
st.markdown("""
<style>
.big-button button {height:60px; font-size:26px; background-color:#4CAF50; color:white; width:100%; margin-top:10px;}
.big-button-red button {height:60px; font-size:26px; background-color:#f44336; color:white; width:100%; margin-top:10px;}
.big-input input {height:55px; font-size:22px; margin-bottom:10px;}
.radio-horizontal .stRadio > label {font-size:22px;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
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
    st.info(f"Aktuálne prihlásený kontrolor: {st.session_state.kontrolor}")
    if st.button("Odhlásiť kontrolóra"):
        st.session_state.kontrolor = ""
        st.experimental_rerun()

st.write("---")

# ---------- FUNKCIA NA FORM ----------
def vykresli_formular():
    key = f"form_{st.session_state.form_key}"

    paleta_id = st.text_input("Číslo palety:", key=f"{key}_paleta_id")
    bd_balenie = st.radio("Ide o BD balenie?", ("Áno", "Nie"), key=f"{key}_bd", horizontal=True)

    manual_count = st.checkbox("Chcem zadať presný počet kusov", key=f"{key}_manual")

    typ_bd = None
    pocet_v_rade = pocet_radov = pocet_volnych = None
    celkovy_pocet_jednotiek = None

    if not manual_count:
        if bd_balenie == "Áno":
            typ_bd = st.text_input("Zadajte typ BD (napr. BD4, BD6):", key=f"{key}_typ_bd")
        pocet_v_rade = st.number_input("Počet krabíc v rade:", min_value=1, step=1, key=f"{key}_v_rade")
        pocet_radov = st.number_input("Počet radov na palete:", min_value=1, step=1, key=f"{key}_radov")
        pocet_volnych = st.number_input("Počet voľných krabíc navrchu:", min_value=0, step=1, key=f"{key}_volne")

        if pocet_v_rade and pocet_radov is not None and pocet_volnych is not None:
            pocet_krabic = pocet_v_rade * pocet_radov + pocet_volnych
            celkovy_pocet_jednotiek = pocet_krabic
            if bd_balenie == "Áno" and typ_bd:
                try:
                    celkovy_pocet_jednotiek *= int(typ_bd.replace("BD", ""))
                except:
                    st.warning("Nepodarilo sa prečítať BD typ, použité 1x")
    else:
        celkovy_pocet_jednotiek = st.number_input("Zadajte presný počet kusov:", min_value=1, step=1, key=f"{key}_exact")

    if st.button("💾 Uložiť", key=f"{key}_ulozit", use_container_width=True):
        if not paleta_id:
            st.error("Zadajte číslo palety!")
            return

        data = {
            "paleta_id": paleta_id,
            "bd": bd_balenie == "Áno",
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
            st.success(f"Paleta {paleta_id} uložená!")
            st.session_state.form_visible = False
        except Exception as e:
            st.error(f"Chyba pri ukladaní: {e}")

# ---------- FORM / NOVÁ PALETA ----------
if st.session_state.form_visible:
    vykresli_formular()
else:
    st.button("➕ Nová paleta", on_click=lambda: (
        st.session_state.update(form_visible=True, form_key=st.session_state.form_key + 1)
    ), use_container_width=True)
