import streamlit as st
from supabase import create_client
from datetime import datetime
# Skrytie hamburger menu a footeru
hide_menu = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)
# ---------- KONFIGURÁCIA ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

# ---------- STYL ----------
st.markdown("""
<style>
.big-button button {
    height:60px;
    font-size:24px;
    background-color:#4CAF50;
    color:white;
    width:100%;
    margin-top:10px;
}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "kontrolor" not in st.session_state:
    st.session_state.kontrolor = ""

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# ---------- LOGIN ----------
if not st.session_state.kontrolor:
    st.session_state.kontrolor = st.text_input("👷‍♂️ Zadajte meno kontrolóra:")

if st.session_state.kontrolor:
    st.info(f"Prihlásený kontrolór: **{st.session_state.kontrolor}**")
    if st.button("Odhlásiť kontrolóra"):
        st.session_state.kontrolor = ""
        st.session_state.form_key += 1
        st.rerun()

st.write("---")

# ---------- FORMULÁR ----------
def vykresli_formular():
    st.subheader("🧾 Nová paleta")

    # 🔁 NOVÁ PALETA = nový form_key
    if st.button("➕ Nová paleta"):
        st.session_state.form_key += 1
        st.rerun()

    key = f"form_{st.session_state.form_key}"

    paleta_id = st.text_input(
        "Číslo palety (naskenujte čiarový kód):",
        key=f"{key}_paleta"
    )

    if not paleta_id:
        st.info("👉 Naskenujte čiarový kód palety.")
        return

    zadanie_typ = st.radio(
        "Ako chcete zadať počet jednotiek?",
        ("Manuálne", "Výpočet podľa vrstiev"),
        horizontal=True,
        key=f"{key}_typ"
    )

    bd_balenie = st.radio(
        "Ide o BD balenie?",
        ("Áno", "Nie"),
        horizontal=True,
        key=f"{key}_bd"
    )

    bd = bd_balenie == "Áno"
    typ_bd = (
        st.text_input("Typ BD (napr. BD4, BD6):", key=f"{key}_typbd")
        if bd else None
    )

    manual_count = None
    celkovy_pocet = None

    if zadanie_typ == "Manuálne":
        manual_count = st.number_input(
            "Zadajte počet jednotiek:",
            min_value=0,
            step=1,
            key=f"{key}_manual"
        )
        celkovy_pocet = manual_count
    else:
        v_rade = st.number_input(
            "Počet krabíc v rade:",
            min_value=1,
            step=1,
            key=f"{key}_vrade"
        )
        radov = st.number_input(
            "Počet radov na palete:",
            min_value=1,
            step=1,
            key=f"{key}_radov"
        )
        volne = st.number_input(
            "Počet voľných krabíc navrchu:",
            min_value=0,
            step=1,
            key=f"{key}_volne"
        )

        celkovy_pocet = v_rade * radov + volne

        if bd and typ_bd:
            try:
                celkovy_pocet *= int(typ_bd.replace("BD", ""))
            except:
                st.warning("⚠️ Neplatný BD typ, použité 1x")

    if st.button("💾 Uložiť paletu", use_container_width=True):
        data = {
            "paleta_id": paleta_id,
            "bd": bd,
            "typ_bd": typ_bd,
            "pocet_v_rade": None,
            "pocet_radov": None,
            "pocet_volnych": None,
            "celkovy_pocet_jednotiek": celkovy_pocet,
            "manual_count": manual_count,
            "kontrolor": st.session_state.kontrolor,
            "datum": datetime.now().isoformat()
        }

        try:
            databaze.table("palety").insert(data).execute()
            st.success(f"✅ Paleta **{paleta_id}** uložená")

            # 🔁 RESET FORMULÁRA
            st.session_state.form_key += 1
            st.rerun()

        except Exception as e:
            st.error("❌ Chyba pri ukladaní")
            st.write(e)

vykresli_formular()
