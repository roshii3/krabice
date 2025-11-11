import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# --------------------------
# Supabase konfigurácia
# --------------------------
url = "https://TVOJ_SUPABASE_URL.supabase.co"
key = "TVOJ_SUPABASE_API_KEY"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Paletový záznam", page_icon="📦", layout="centered")

st.title("📦 Záznam palety")

# --------------------------
# Základné údaje
# --------------------------
st.subheader("Základné údaje")

paleta_id = st.text_input("Paleta ID (z čítačky čiarového kódu):")

typ_bd = st.selectbox("Je to BD?", ["Áno", "Nie"])
bd = True if typ_bd == "Áno" else False

manual_mode = st.radio("Ako chceš zadať počet jednotiek?", ["Automaticky (výpočet)", "Manuálne"])

# --------------------------
# Výpočet alebo manuálny vstup
# --------------------------
if manual_mode == "Automaticky (výpočet)":
    pocet_v_rade = st.number_input("Počet v rade", min_value=1, step=1)
    pocet_radov = st.number_input("Počet radov", min_value=1, step=1)
    pocet_volnych = st.number_input("Počet voľných jednotiek (ak sú)", min_value=0, step=1)

    celkovy_pocet_jednotiek = (pocet_v_rade * pocet_radov) + pocet_volnych
else:
    celkovy_pocet_jednotiek = st.number_input("Zadaj celkový počet jednotiek manuálne", min_value=1, step=1)

kontrolor = st.text_input("Meno kontrolóra:")
datum = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --------------------------
# Uloženie do DB
# --------------------------
if st.button("💾 Uložiť záznam"):
    if not paleta_id:
        st.warning("⚠️ Zadaj ID palety (oskenuj čiarový kód).")
    elif not kontrolor:
        st.warning("⚠️ Zadaj meno kontrolóra.")
    else:
        data = {
            "paleta_id": paleta_id,
            "bd": bd,
            "typ_bd": typ_bd,
            "pocet_v_rade": None if manual_mode == "Manuálne" else pocet_v_rade,
            "pocet_radov": None if manual_mode == "Manuálne" else pocet_radov,
            "pocet_volnych": None if manual_mode == "Manuálne" else pocet_volnych,
            "celkovy_pocet_jednotiek": celkovy_pocet_jednotiek,
            "manual_count": (manual_mode == "Manuálne"),
            "kontrolor": kontrolor,
            "datum": datum
        }

        try:
            supabase.table("palety").insert(data).execute()
            st.success("✅ Záznam úspešne uložený.")
        except Exception as e:
            st.error(f"⚠️ Chyba pri ukladaní do databázy: {e}")
