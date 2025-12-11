import streamlit as st
from supabase import create_client
from datetime import datetime

# ---------- KONFIGURÁCIA ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

# ---------- STYL ----------
st.markdown("""
<style>
.big-button button {height:60px; font-size:24px; background-color:#4CAF50; color:white; width:100%; margin-top:10px;}
.big-input input {height:55px; font-size:22px; margin-bottom:10px;}
.radio-horizontal .stRadio > label {font-size:22px;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "kontrolor" not in st.session_state:
    st.session_state.kontrolor = ""

if not st.session_state.kontrolor:
    st.session_state.kontrolor = st.text_input("👷‍♂️ Zadajte meno kontrolóra:")

if st.session_state.kontrolor:
    st.info(f"Prihlásený kontrolór: **{st.session_state.kontrolor}**")
    if st.button("Odhlásiť"):
        st.session_state.clear()
        st.rerun()

st.write("---")


# ---------- RESET FORMULÁRA ----------
def reset_form():
    kontrolor = st.session_state.kontrolor
    st.session_state.clear()
    st.session_state.kontrolor = kontrolor
    st.rerun()


# ---------- FORMULÁR ----------
def vykresli_formular():
    st.subheader("🧾 Nová paleta")

    # RESET tlačidlo – funguje vždy
    if st.button("🔄 Nová paleta"):
        reset_form()

    paleta_id = st.text_input("Číslo palety (naskenujte čiarový kód):", key="paleta_id")

    if not paleta_id:
        st.info("👉 Naskenujte čiarový kód alebo zadajte číslo palety.")
        return

    zadanie_typ = st.radio(
        "Ako chcete zadať počet jednotiek?",
        ("Manuálne", "Výpočet podľa vrstiev"),
        key="zadanie_typ",
        horizontal=True
    )

    bd_balenie = st.radio("Ide o BD balenie?", ("Áno", "Nie"), horizontal=True)
    bd = bd_balenie == "Áno"
    typ_bd = st.text_input("Typ BD (napr. BD4, BD6):", key="typ_bd") if bd else None

    manual_count = None
    celkovy_pocet_jednotiek = None

    if zadanie_typ == "Manuálne":
        manual_count = st.number_input("Zadajte počet jednotiek:", min_value=0, step=1, key="manual_count")
        celkovy_pocet_jednotiek = manual_count
    else:
        pocet_v_rade = st.number_input("Počet krabíc v rade:", min_value=1, step=1, key="v_rade")
        pocet_radov = st.number_input("Počet radov na palete:", min_value=1, step=1, key="radov")
        pocet_volnych = st.number_input("Počet voľných krabíc navrchu:", min_value=0, step=1, key="volne")
        celkovy_pocet_jednotiek = pocet_v_rade * pocet_radov + pocet_volnych

        if bd and typ_bd:
            try:
                celkovy_pocet_jednotiek *= int(typ_bd.replace("BD", ""))
            except:
                st.warning("⚠️ Nepodarilo sa rozpoznať typ BD, použité 1x")

    if st.button("💾 Uložiť paletu", use_container_width=True):
        if not paleta_id:
            st.error("❌ Zadajte alebo naskenujte číslo palety!")
            return

        data = {
            "paleta_id": paleta_id,
            "bd": bd,
            "typ_bd": typ_bd,
            "pocet_v_rade": None,
            "pocet_radov": None,
            "pocet_volnych": None,
            "celkovy_pocet_jednotiek": celkovy_pocet_jednotiek,
            "manual_count": manual_count,
            "kontrolor": st.session_state.kontrolor,
            "datum": datetime.now().isoformat()
        }

        try:
            databaze.table("palety").insert(data).execute()
            st.success(f"✅ Paleta {paleta_id} bola uložená!")
            reset_form()

        except Exception as e:
            st.error("⚠️ Chyba pri ukladaní!")
            st.write(e)


vykresli_formular()
