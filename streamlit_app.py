import streamlit as st
from supabase import create_client
from datetime import datetime

# ---------- KONFIGURÁCIA ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

st.set_page_config(page_title="Paletový záznam", page_icon="📦", layout="centered")

# ---------- STYL ----------
st.markdown("""
<style>
.big-button button {height:56px; font-size:22px; background-color:#4CAF50; color:white; width:100%; margin-top:8px;}
.big-input input {height:50px; font-size:20px; margin-bottom:8px;}
.radio-horizontal .stRadio > label {font-size:20px;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION INIT ----------
if "kontrolor" not in st.session_state:
    st.session_state.kontrolor = ""

# reset counter (used to generate fresh keys for inputs)
if "reset_form" not in st.session_state:
    st.session_state.reset_form = 0

# ---------- LOGIN (kontrolór zostane prihlásený pri resete) ----------
st.title("📦 Paletový záznam")
if not st.session_state.kontrolor:
    st.session_state.kontrolor = st.text_input("👷‍♂️ Zadajte meno kontrolóra:", key="kontrolor_input")

if st.session_state.kontrolor:
    st.info(f"Prihlásený kontrolór: **{st.session_state.kontrolor}**")
    if st.button("Odhlásiť kontrolóra"):
        # kompletné vyčistenie session (vrátane reset countera)
        st.session_state.clear()
        st.experimental_rerun()

st.write("---")

# ---------- NOVÁ PALETA TLAČIDLO (reset) ----------
if st.button("🆕 Nová paleta"):
    st.session_state.reset_form += 1
    st.experimental_rerun()

# key suffix pre všetky inputy, aby sa dali resetovať
key_suffix = f"_{st.session_state.reset_form}"

# ---------- FORMULÁR ----------
st.subheader("🧾 Nová paleta (scan čiarového kódu / ručné zadanie)")

paleta_id = st.text_input(
    "Číslo palety (naskenujte čiarový kód alebo zadajte manuálne):",
    key="paleta_id" + key_suffix,
    placeholder="Naskenujte čiarový kód alebo zadajte číslo..."
)

# ak nie je paleta zadaná, zobrazíme len info (aby kontrolór mohol najprv naskenovať)
if not paleta_id:
    st.info("👉 Naskenujte čiarový kód alebo zadajte číslo palety.")
    st.stop()

# Spôsob zadania počtu
zadanie_typ = st.radio(
    "Ako chcete zadať počet jednotiek?",
    ("Manuálne", "Výpočet podľa vrstiev"),
    index=0,
    key="zadanie_typ" + key_suffix,
    horizontal=True
)

# BD info (vždy dostupné)
bd_balenie = st.radio(
    "Ide o BD balenie?",
    ("Áno", "Nie"),
    index=1,
    key="bd" + key_suffix,
    horizontal=True
)
bd = True if bd_balenie == "Áno" else False

# typ_bd iba ak BD = Áno
typ_bd = None
if bd:
    typ_bd = st.text_input(
        "Typ BD (napr. BD4, BD6) — nechajte prázdne ak nevieme:",
        key="typ_bd" + key_suffix
    )
    # zabezpečíme, že ak používateľ zadá iba číslo, uložíme ako text (DB typ text)
    if typ_bd is not None:
        typ_bd = str(typ_bd).strip() or None

# Polia podľa režimu
manual_count = None
celkovy_pocet_jednotiek = None
pocet_v_rade = pocet_radov = pocet_volnych = None

if zadanie_typ == "Manuálne":
    manual_count = st.number_input(
        "Zadajte počet jednotiek (manuálne):",
        min_value=0,
        step=1,
        key="manual_count" + key_suffix
    )
    celkovy_pocet_jednotiek = int(manual_count) if manual_count is not None else None
else:
    pocet_v_rade = st.number_input("Počet krabíc v rade:", min_value=1, step=1, key="v_rade" + key_suffix)
    pocet_radov = st.number_input("Počet radov na palete:", min_value=1, step=1, key="radov" + key_suffix)
    pocet_volnych = st.number_input("Počet voľných krabíc navrchu:", min_value=0, step=1, key="volne" + key_suffix)

    # bezpečný výpočet (len ak všetky polia majú hodnotu)
    try:
        pocet_v_rade_i = int(pocet_v_rade)
        pocet_radov_i = int(pocet_radov)
        pocet_volnych_i = int(pocet_volnych)
        pocet_krabic = pocet_v_rade_i * pocet_radov_i + pocet_volnych_i
        celkovy_pocet_jednotiek = pocet_krabic
        # ak BD, aplikuj faktor (ak sa zadal)
        if bd and typ_bd:
            try:
                faktor = int(str(typ_bd).replace("BD", "").strip())
                celkovy_pocet_jednotiek = int(celkovy_pocet_jednotiek) * faktor
            except Exception:
                # ak sa nepodarí parsovať faktor, nechaj pôvodný počet (bez násobenia)
                st.warning("⚠️ Typ BD nerozpoznaný ako BD<number>, nepoužije sa násobenie.")
    except Exception:
        celkovy_pocet_jednotiek = None
        st.error("⚠️ Chyba vo výpočte: skontrolujte hodnoty počtu v rade / radov / voľných.")

# ---------- ULOŽENIE ----------
if st.button("💾 Uložiť paletu", use_container_width=True):
    # validácia
    if not paleta_id:
        st.error("❌ Zadajte alebo naskenujte číslo palety!")
    elif st.session_state.kontrolor == "":
        st.error("❌ Zadajte meno kontrolóra (hore).")
    else:
        # pripraviť dáta konzistentne s DB schémou
        data = {
            "paleta_id": str(paleta_id),
            "bd": bool(bd),
            "typ_bd": str(typ_bd) if typ_bd else None,
            "pocet_v_rade": int(pocet_v_rade) if pocet_v_rade is not None and zadanie_typ != "Manuálne" else None,
            "pocet_radov": int(pocet_radov) if pocet_radov is not None and zadanie_typ != "Manuálne" else None,
            "pocet_volnych": int(pocet_volnych) if pocet_volnych is not None and zadanie_typ != "Manuálne" else None,
            "celkovy_pocet_jednotiek": int(celkovy_pocet_jednotiek) if celkovy_pocet_jednotiek is not None else None,
            "manual_count": int(manual_count) if manual_count is not None else None,
            "kontrolor": str(st.session_state.kontrolor),
            "datum": datetime.now().isoformat()
        }

        try:
            databaze.table("palety").insert(data).execute()
            st.success(f"✅ Paleta **{paleta_id}** bola uložená.")
            # po úspešnom uložení spravíme reset formulára zvýšením counteru a rerun
            st.session_state.reset_form += 1
            st.experimental_rerun()

        except Exception as e:
            st.error("⚠️ Chyba pri ukladaní do databázy.")
            st.write(e)

# ---------- VOLITEĽNÉ: zobraziť posledných 10 záznamov (pre kontrolu) ----------
st.write("---")
st.subheader("Posledné palety (pre kontrolu)")
try:
    posledne = databaze.table("palety").select("*").order("datum", desc=True).limit(10).execute()
    if getattr(posledne, "data", None):
        for p in posledne.data:
            bd_label = "Áno" if p.get("bd") else "Nie"
            st.write(f"• {p.get('paleta_id')} — Jednotiek: {p.get('celkovy_pocet_jednotiek')} — BD: {bd_label} — {p.get('kontrolor')} — {str(p.get('datum'))[:19]}")
    else:
        st.info("Zatiaľ žiadne záznamy.")
except Exception as e:
    st.error("Nepodarilo sa načítať posledné palety.")
    # nezobrazujeme full exception pre bezpečnosť, ale ukážeme stručný detail
    st.write(e)
