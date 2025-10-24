import streamlit as st
from supabase import create_client, Client
import datetime

# ---------- KONFIGURÁCIA ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

st.set_page_config(page_title="Palety", page_icon="📦", layout="centered")

# ---------- FUNKCIE ----------
def uloz_paletu(data: dict):
    try:
        databaze.table("palety").insert(data).execute()
        st.success("✅ Paleta bola úspešne uložená!")
    except Exception as e:
        st.error(f"Chyba pri ukladaní: {e}")

def reset_paletovy_formular():
    st.session_state["paleta_id"] = ""
    st.session_state["bd_typ"] = ""
    st.session_state["bd_rady"] = ""
    st.session_state["bd_pocet"] = ""
    st.session_state["bd_volne"] = ""
    st.session_state["bd"] = None
    st.session_state["krok"] = 2

# ---------- RIADENIE KROKOV ----------
if "krok" not in st.session_state:
    st.session_state["krok"] = 1

# ---------- KROK 1 – MENO (QR SKEN) ----------
if st.session_state["krok"] == 1:
    st.title("👷‍♂️ Identifikácia kontrolóra")

   
    meno = st.text_input("Skenuj QR kód s menom", key="meno_input", placeholder="Naskenuj meno...")
    if meno:
        st.session_state["meno"] = meno
        st.session_state["krok"] = 2
        st.rerun()


# ---------- KROK 2 – ČÍSLO PALETY ----------
elif st.session_state["krok"] == 2:
    st.title("📦 Zadaj číslo palety")

    paleta_id = st.text_input("Skenuj čiarový kód palety", key="paleta_id", placeholder="Skenuj alebo zadaj...")

    st.markdown("### Alebo použi dotykovú klávesnicu:")
    cols = st.columns(3)
    for i, cislo in enumerate(["1","2","3","4","5","6","7","8","9","0"]):
        if cols[i % 3].button(cislo, use_container_width=True):
            st.session_state["paleta_id"] = st.session_state.get("paleta_id", "") + cislo
            st.rerun()

    colA, colB = st.columns(2)
    if colA.button("❌ Storno", use_container_width=True):
        st.session_state["paleta_id"] = ""
        st.rerun()
    if colB.button("✅ Potvrdiť", use_container_width=True):
        if st.session_state.get("paleta_id"):
            st.session_state["krok"] = 3
            st.rerun()
        else:
            st.warning("Najprv zadaj číslo palety.")

# ---------- KROK 3 – BD ÁNO/NIE ----------
elif st.session_state["krok"] == 3:
    st.title("🧱 BD kontrola")

    st.write("Je na palete BD?")
    col1, col2 = st.columns(2)
    if col1.button("✅ ÁNO", use_container_width=True):
        st.session_state["bd"] = True
        st.session_state["krok"] = 4
        st.rerun()
    if col2.button("❌ NIE", use_container_width=True):
        st.session_state["bd"] = False
        st.session_state["krok"] = 5
        st.rerun()

# ---------- KROK 4 – BD DETAILY ----------
elif st.session_state["krok"] == 4:
    st.title("📋 Zadaj údaje o BD")

    st.session_state["bd_typ"] = st.text_input("Typ BD", key="bd_typ")
    st.session_state["bd_rady"] = st.number_input("Počet radov", min_value=0, step=1, key="bd_rady")
    st.session_state["bd_pocet"] = st.number_input("Počet v rade", min_value=0, step=1, key="bd_pocet")
    st.session_state["bd_volne"] = st.number_input("Voľné miesta", min_value=0, step=1, key="bd_volne")

    colA, colB = st.columns(2)
    if colA.button("🔙 Späť", use_container_width=True):
        st.session_state["krok"] = 3
        st.rerun()
    if colB.button("✅ Ďalej", use_container_width=True):
        st.session_state["krok"] = 5
        st.rerun()

# ---------- KROK 5 – POTVRDENIE ----------
elif st.session_state["krok"] == 5:
    st.title("✅ Potvrdenie údajov")

    st.write("Skontroluj zadané údaje:")
    st.markdown(f"**Meno:** {st.session_state.get('meno', '')}")
    st.markdown(f"**Paleta:** {st.session_state.get('paleta_id', '')}")
    st.markdown(f"**BD:** {'ÁNO' if st.session_state.get('bd') else 'NIE'}")

    if st.session_state.get("bd"):
        st.markdown(f"**Typ BD:** {st.session_state.get('bd_typ', '')}")
        st.markdown(f"**Rady:** {st.session_state.get('bd_rady', 0)}")
        st.markdown(f"**V rade:** {st.session_state.get('bd_pocet', 0)}")
        st.markdown(f"**Voľné:** {st.session_state.get('bd_volne', 0)}")

    col1, col2 = st.columns(2)
    if col1.button("🔙 Späť", use_container_width=True):
        if st.session_state.get("bd"):
            st.session_state["krok"] = 4
        else:
            st.session_state["krok"] = 3
        st.rerun()

    if col2.button("💾 Uložiť", use_container_width=True):
        data = {
            "datum": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "meno": st.session_state.get("meno"),
            "paleta_id": st.session_state.get("paleta_id"),
            "bd": st.session_state.get("bd"),
            "bd_typ": st.session_state.get("bd_typ"),
            "bd_rady": st.session_state.get("bd_rady"),
            "bd_pocet": st.session_state.get("bd_pocet"),
            "bd_volne": st.session_state.get("bd_volne"),
        }
        uloz_paletu(data)
        reset_paletovy_formular()
        st.success("Nová paleta môže byť naskenovaná.")
