import streamlit as st
import streamlit.components.v1 as components

def barcode_scanner(key=None):
    """
    Zobrazí kameru a dekóduje čiarový kód pomocou QuaggaJS.
    Výstup sa vloží do textového poľa (paleta_id).
    """
    components.html(
        f"""
        <div>
            <video id="video" width="300" height="200" style="border:1px solid black"></video>
            <p id="result"></p>
        </div>
        <script src="https://unpkg.com/@ericblade/quagga2/dist/quagga.js"></script>
        <script>
        const resultEl = document.getElementById("result");
        Quagga.init({{
            inputStream : {{
                name : "Live",
                type : "LiveStream",
                target: document.querySelector('#video'),
                constraints: {{
                    facingMode: "environment"
                }}
            }},
            decoder : {{
                readers : ["code_128_reader","ean_reader","ean_8_reader","code_39_reader"]
            }}
        }}, function(err) {{
            if (err) {{ console.log(err); return }}
            Quagga.start();
        }});
        Quagga.onDetected(function(data){{
            const code = data.codeResult.code;
            resultEl.innerText = "Naskenované: " + code;
            const input = window.parent.document.querySelector("input[data-key='{key}']");
            if(input) input.value = code;
        }});
        </script>
        """,
        height=300
    )
    return st.text_input("Paleta ID (autofill z kamery):", key=key)

import streamlit as st
from supabase import create_client
from datetime import datetime
from barcode_component.my_barcode_component import barcode_scanner

# ---------- CONFIG ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
databaze = create_client(DATABAZA_URL, DATABAZA_KEY)

# ---------- SESSION ----------
if "kontrolor" not in st.session_state:
    st.session_state.kontrolor = ""

if not st.session_state.kontrolor:
    st.session_state.kontrolor = st.text_input("Zadajte meno kontrolóra:")

if st.session_state.kontrolor:
    st.info(f"Aktuálne prihlásený kontrolór: {st.session_state.kontrolor}")

st.write("---")

# ---------- FORM ----------
def vykresli_formular():
    paleta_id = barcode_scanner(key="paleta_id")  # komponent s kamerou

    if paleta_id:
        st.write(f"Naskenovaná paleta: {paleta_id}")

    # BD info
    bd_balenie = st.radio("Ide o BD balenie?", ("Áno", "Nie"), key="bd")
    bd = bd_balenie == "Áno"
    typ_bd = st.text_input("Typ BD:", key="typ_bd") if bd else None

    # Spôsob zadania
    zadanie_typ = st.radio("Spôsob zadania:", ("Manuálne", "Výpočet podľa vrstiev"), key="zadanie")

    manual_count = None
    celkovy_pocet_jednotiek = None
    if zadanie_typ == "Manuálne":
        manual_count = st.number_input("Počet jednotiek:", min_value=0, step=1, key="manual")
    else:
        pocet_v_rade = st.number_input("Počet krabíc v rade:", min_value=1, step=1, key="v_rade")
        pocet_radov = st.number_input("Počet radov na palete:", min_value=1, step=1, key="radov")
        pocet_volnych = st.number_input("Počet voľných krabíc navrchu:", min_value=0, step=1, key="volne")
        celkovy_pocet_jednotiek = pocet_v_rade*pocet_radov + pocet_volnych
        if bd and typ_bd:
            try:
                celkovy_pocet_jednotiek *= int(typ_bd.replace("BD",""))
            except:
                st.warning("Nepodarilo sa rozpoznať typ BD, použité 1x")

    if st.button("💾 Uložiť"):
        if not paleta_id:
            st.error("Paleta nie je naskenovaná!")
            return

        data = {
            "paleta_id": paleta_id,
            "bd": bd,
            "typ_bd": typ_bd,
            "celkovy_pocet_jednotiek": celkovy_pocet_jednotiek,
            "manual_count": manual_count,
            "kontrolor": st.session_state.kontrolor,
            "datum": datetime.now().isoformat()
        }

        try:
            databaze.table("palety").insert(data).execute()
            st.success("Paleta uložená ✅")
        except Exception as e:
            st.error("⚠️ Chyba pri ukladaní do databázy")
            st.write(e)

vykresli_formular()

