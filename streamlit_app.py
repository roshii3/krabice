import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# ---------- CONFIG ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

# ---------- SESSION STATE ----------
if "kontrolor" not in st.session_state:
    st.session_state.kontrolor = ""
if "last_active" not in st.session_state:
    st.session_state.last_active = datetime.now()
if "step" not in st.session_state:
    st.session_state.step = "kontrolor"  # kroky: kontrolor → paleta → bd → pocty → ulozit
if "form_data" not in st.session_state:
    st.session_state.form_data = {}

# ---------- AUTO LOGOUT po 30 min ----------
if st.session_state.kontrolor:
    if datetime.now() - st.session_state.last_active > timedelta(minutes=30):
        st.warning("Kontrolor bol odhlásený po 30 min nečinnosti.")
        st.session_state.kontrolor = ""
        st.session_state.step = "kontrolor"

# ---------- NAVIGATION ----------
def go_to(step):
    st.session_state.step = step
    st.session_state.last_active = datetime.now()

# ---------- KONTROLOR ----------
if st.session_state.step == "kontrolor":
    st.title("Prihlásenie kontrolóra")
    if st.session_state.kontrolor:
        st.info(f"Aktuálne prihlásený kontrolor: {st.session_state.kontrolor}")
        if st.button("Odhlásiť kontrolóra"):
            st.session_state.kontrolor = ""
            st.experimental_rerun()
    else:
        name = st.text_input("Zadajte meno kontrolóra", key="kontrolor_input", placeholder="QR alebo ručne")
        if name:
            st.session_state.kontrolor = name
            go_to("paleta")
            st.experimental_rerun()

# ---------- PALETA ----------
elif st.session_state.step == "paleta":
    st.title("1️⃣ Číslo palety")
    st.write("Naskenujte čiarový kód alebo zadajte číslo palety cez numerickú klávesnicu.")

    paleta = st.text_input("Číslo palety", key="paleta_input", value=st.session_state.form_data.get("paleta_id",""), placeholder="Paleta ID")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Späť"):
            go_to("kontrolor")
            st.experimental_rerun()
    with col2:
        if paleta and st.button("Potvrdiť"):
            st.session_state.form_data["paleta_id"] = paleta
            go_to("bd")
            st.experimental_rerun()

# ---------- BD ----------
elif st.session_state.step == "bd":
    st.title("2️⃣ BD balenie")
    bd = st.radio("Ide o BD balenie?", ("Áno","Nie"), key="bd_radio", index=0 if st.session_state.form_data.get("bd_balenie")=="Áno" else 1)
    typ_bd = None
    if bd == "Áno":
        typ_bd = st.text_input("Zadajte typ BD (napr. BD4, BD6)", key="typ_bd_input", value=st.session_state.form_data.get("typ_bd",""))
    else:
        st.session_state.form_data["typ_bd"] = ""

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Späť"):
            go_to("paleta")
            st.experimental_rerun()
    with col2:
        if st.button("Potvrdiť"):
            st.session_state.form_data["bd_balenie"] = bd
            if bd=="Áno":
                st.session_state.form_data["typ_bd"] = typ_bd
            go_to("pocty")
            st.experimental_rerun()

# ---------- POČTY ----------
elif st.session_state.step == "pocty":
    st.title("3️⃣ Počet krabíc")
    pocet_v_rade = st.number_input("Počet krabíc v rade", min_value=1, step=1, key="pocet_v_rade_input", value=st.session_state.form_data.get("pocet_v_rade",1))
    pocet_radov = st.number_input("Počet radov", min_value=1, step=1, key="pocet_radov_input", value=st.session_state.form_data.get("pocet_radov",1))
    pocet_volnych = st.number_input("Počet voľných krabíc navrchu", min_value=0, step=1, key="pocet_volnych_input", value=st.session_state.form_data.get("pocet_volnych",0))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Späť"):
            go_to("bd")
            st.experimental_rerun()
    with col2:
        if st.button("Potvrdiť"):
            st.session_state.form_data["pocet_v_rade"] = pocet_v_rade
            st.session_state.form_data["pocet_radov"] = pocet_radov
            st.session_state.form_data["pocet_volnych"] = pocet_volnych
            go_to("ulozit")
            st.experimental_rerun()

# ---------- ULOŽIŤ ----------
elif st.session_state.step == "ulozit":
    st.title("4️⃣ Potvrdenie a uloženie")
    fd = st.session_state.form_data
    pocet_krabic = fd["pocet_v_rade"] * fd["pocet_radov"] + fd["pocet_volnych"]
    celkovy_pocet_jednotiek = pocet_krabic
    if fd.get("bd_balenie")=="Áno" and fd.get("typ_bd"):
        try:
            celkovy_pocet_jednotiek *= int(fd["typ_bd"].replace("BD",""))
        except:
            st.warning("Nepodarilo sa prečítať BD typ. Predpokladám 1 jednotku na krabicu.")

    st.write("**Kontrolor:**", st.session_state.kontrolor)
    st.write("**Paleta:**", fd["paleta_id"])
    st.write("**BD balenie:**", fd.get("bd_balenie"))
    st.write("**Typ BD:**", fd.get("typ_bd",""))
    st.write("**Počet krabíc v rade:**", fd["pocet_v_rade"])
    st.write("**Počet radov:**", fd["pocet_radov"])
    st.write("**Počet voľných:**", fd["pocet_volnych"])
    st.write("**Celkový počet jednotiek:**", celkovy_pocet_jednotiek)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Späť"):
            go_to("pocty")
            st.experimental_rerun()
    with col2:
        if st.button("Uložiť"):
            # --- uloženie do Supabase ---
            data = {
                "paleta_id": fd["paleta_id"],
                "pocet_v_rade": fd["pocet_v_rade"],
                "pocet_radov": fd["pocet_radov"],
                "pocet_volnych": fd["pocet_volnych"],
                "typ_balika": fd.get("typ_bd"),
                "pocet_krabic": pocet_krabic,
                "celkovy_pocet_jednotiek": celkovy_pocet_jednotiek,
                "kontrolor": st.session_state.kontrolor,
                "datum": datetime.now().isoformat()
            }
            databaze.table("palety").insert(data).execute()
            # --- log ---
            log_data = {
                "paleta_id": fd["paleta_id"],
                "akcia": f"Vytvorená paleta: {fd['paleta_id']}, BD: {fd.get('typ_bd','')}, {fd['pocet_v_rade']}x{fd['pocet_radov']}, voľné: {fd['pocet_volnych']}, celk. jednotky: {celkovy_pocet_jednotiek}",
                "kontrolor": st.session_state.kontrolor,
                "datum": datetime.now().isoformat()
            }
            databaze.table("palety_log").insert(log_data).execute()

            st.success("Údaje boli uložené.")
            st.session_state.form_data = {}
            go_to("paleta")
            st.experimental_rerun()
