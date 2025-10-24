# streamlit_app.py
# Aplikácia pre SBS (jednoduché kroky, veľké tlačidlá, on-screen keypad)
# Nastav v Streamlit secrets: DATABAZA_URL, DATABAZA_KEY

import streamlit as st
from supabase import create_client
from datetime import datetime

# ---------- CONFIG ----------
DATABAZA_URL = st.secrets["DATABAZA_URL"]
DATABAZA_KEY = st.secrets["DATABAZA_KEY"]
db = create_client(DATABAZA_URL, DATABAZA_KEY)

# ---------- UTILITY / STYLING ----------
st.set_page_config(page_title="SBS Palety", layout="centered")
st.markdown(
    """
    <style>
    .big-btn button {height:64px; font-size:26px; border-radius:12px;}
    .kbd-btn button {height:70px; width:80px; font-size:28px; border-radius:12px; margin:6px;}
    .num-display {font-size:30px; height:60px; border-radius:8px; padding:10px; background:#f1f3f4}
    .step-title {font-size:28px; font-weight:600;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- SESSION STATE INIT ----------
if "screen" not in st.session_state:
    st.session_state.screen = "home"  # home, paleta, kontrolor, bd, counts, summary
if "form_id" not in st.session_state:
    st.session_state.form_id = 0
# values (kept between screens)
for k in ("paleta_val", "kontrolor_val", "bd_choice", "bd_type_val",
          "pocet_v_rade_val", "pocet_radov_val", "pocet_volnych_val"):
    if k not in st.session_state:
        st.session_state[k] = "" if "val" in k or "type" in k else "Nie"
# keypad target: which field is receiving keypad input
if "keypad_target" not in st.session_state:
    st.session_state.keypad_target = None
# camera image holders
if "paleta_image" not in st.session_state:
    st.session_state.paleta_image = None
if "kontrolor_image" not in st.session_state:
    st.session_state.kontrolor_image = None

# ---------- HELPERS ----------
def go_to(screen_name):
    st.session_state.screen = screen_name

def clear_form():
    st.session_state.paleta_val = ""
    st.session_state.kontrolor_val = ""
    st.session_state.bd_choice = "Nie"
    st.session_state.bd_type_val = ""
    st.session_state.pocet_v_rade_val = ""
    st.session_state.pocet_radov_val = ""
    st.session_state.pocet_volnych_val = ""
    st.session_state.paleta_image = None
    st.session_state.kontrolor_image = None
    st.session_state.keypad_target = None
    st.session_state.form_id += 1
    st.session_state.screen = "home"

def keypad_append(ch):
    t = st.session_state.keypad_target
    if not t:
        return
    # ensure string types
    cur = str(st.session_state.get(t, ""))
    if ch == "←":
        cur = cur[:-1]
    elif ch == "C":
        cur = ""
    elif ch == "Potvrď":  # on-screen confirm for keypad
        # do nothing special here; user will press Next in UI
        return
    else:
        # append digits or letters
        cur = cur + str(ch)
    st.session_state[t] = cur

def render_keypad(digits_layout=None):
    """Renders keypad; digits_layout is list of lists for rows,
    digits can be str '1','2'.. or 'C' (clear), '←' (backspace), 'Potvrď'"""
    if digits_layout is None:
        digits_layout = [["1","2","3"], ["4","5","6"], ["7","8","9"], ["C","0","←"], ["Potvrď"]]
    cols = st.columns(3)
    for r in digits_layout:
        if len(r) == 1:
            c = st.columns([1,2,1])
            with c[1]:
                if st.button(r[0], key=f"kbd_{r[0]}_{st.session_state.form_id}", help=r[0], use_container_width=True):
                    keypad_append(r[0])
            st.write("")  # spacer
        else:
            # distribute across 3 columns
            for i, val in enumerate(r):
                with cols[i]:
                    if st.button(val, key=f"kbd_{val}_{st.session_state.form_id}", use_container_width=True):
                        keypad_append(val)
            cols = st.columns(3)  # new cols for next row

def show_topbar(back_visible=True, title=""):
    st.markdown(f"<div class='step-title'>{title}</div>", unsafe_allow_html=True)
    if back_visible:
        if st.button("◀ Späť", key=f"back_{st.session_state.form_id}"):
            # simple back navigation map
            s = st.session_state.screen
            if s == "paleta":
                go_to("home")
            elif s == "kontrolor":
                go_to("paleta")
            elif s == "bd":
                go_to("kontrolor")
            elif s == "counts":
                go_to("bd")
            elif s == "summary":
                go_to("counts")
            else:
                go_to("home")
            # stop here so the rest of UI doesn't render twice
            st.experimental_rerun()

# ---------- SCREENS ----------
def screen_home():
    st.write("")
    st.markdown("<h2 style='font-size:28px'>Vitajte — zadajte paletu</h2>", unsafe_allow_html=True)
    st.write("Pracovný postup: 1) Paleta → 2) Kontrolor → 3) BD → 4) Počty → 5) Uložiť")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Nová paleta", key="home_new", use_container_width=True):
            clear_form()
            go_to("paleta")
            st.experimental_rerun()
    with c2:
        if st.button("📋 Zobraziť posledné záznamy", key="home_list", use_container_width=True):
            # jednoduchý prehľad posledných 10 z DB
            try:
                res = db.table("palety").select("*").order("datum", desc=True).limit(10).execute()
                rows = res.data
                st.write(rows)
            except Exception as e:
                st.error(f"Chyba pri načítaní: {e}")
from pyzbar.pyzbar import decode
from PIL import Image

def screen_paleta():
    show_topbar(back_visible=True, title="1. Paleta")
    st.write("Naskenujte číslo palety cez čiarový kód alebo zadajte cez numerickú klávesnicu.")

    col_left, col_right = st.columns([2,1])
    with col_left:
        img = st.camera_input("Odfotiť barcode palety", key=f"cam_pal_{st.session_state.form_id}")
        if img is not None:
            st.session_state.paleta_image = img
            st.image(img, caption="Náhľad skenu")
            
            # dekódovanie barcode
            pil_image = Image.open(img)
            decoded = decode(pil_image)
            if decoded:
                st.session_state.paleta_val = decoded[0].data.decode("utf-8")
                st.success(f"Číslo palety prečítané: {st.session_state.paleta_val}")
                if st.button("Pokračovať", key=f"use_pal_img_{st.session_state.form_id}"):
                    go_to("kontrolor")
                    st.experimental_rerun()
            else:
                st.warning("Nepodarilo sa prečítať čiarový kód. Skúste znovu.")


def screen_kontrolor():
    show_topbar(back_visible=True, title="2. Kontrolor")
    st.write("Naskenujte QR s menom kontrolóra alebo zadajte meno cez veľkú klávesnicu (A-Z).")
    col_l, col_r = st.columns([2,1])
    with col_l:
        img = st.camera_input("Odfotiť QR (meno)", key=f"cam_kon_{st.session_state.form_id}")
        if img is not None:
            st.session_state.kontrolor_image = img
            st.image(img, caption="Náhľad skenu")
            if st.button("Použiť tento sken ako meno", key=f"use_kon_img_{st.session_state.form_id}"):
                st.session_state.kontrolor_val = "<SKEN_MENO>"
                go_to("bd")
                st.experimental_rerun()
    with col_r:
        st.markdown("**Meno kontrolóra**")
        st.text_input("", value=st.session_state.kontrolor_val, key=f"display_kon_{st.session_state.form_id}", disabled=True)
        if st.button("Zadať meno (klávesnica)", key=f"enter_kon_{st.session_state.form_id}", use_container_width=True):
            st.session_state.keypad_target = "kontrolor_val"
            st.experimental_rerun()
    if st.session_state.keypad_target == "kontrolor_val":
        st.write("Použite veľkú klávesnicu pre meno (písmená + medzera):")
        # simple alphabet keypad rows
        rows = [
            list("ABCDEF"), list("GHIJKL"), list("MNOPQR"), list("STUVWX"), list("YZ -")
        ]
        # render simple letter buttons (compact)
        for r in rows:
            cols = st.columns(len(r))
            for i, ch in enumerate(r):
                with cols[i]:
                    if st.button(ch, key=f"alpha_{ch}_{st.session_state.form_id}"):
                        # map '-' to space
                        if ch == "-":
                            st.session_state.kontrolor_val += " "
                        else:
                            st.session_state.kontrolor_val += ch
        # small control row
        c1,c2,c3 = st.columns([1,1,1])
        with c1:
            if st.button("←", key=f"kon_bk_{st.session_state.form_id}"):
                st.session_state.kontrolor_val = st.session_state.kontrolor_val[:-1]
        with c2:
            if st.button("C", key=f"kon_clear_{st.session_state.form_id}"):
                st.session_state.kontrolor_val = ""
        with c3:
            if st.button("Hotovo", key=f"kon_done_{st.session_state.form_id}"):
                st.session_state.keypad_target = None
                go_to("bd")
                st.experimental_rerun()

def screen_bd():
    show_topbar(back_visible=True, title="3. BD balenie")
    st.write("Je to BD balenie? (áno/nie)")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Áno", key=f"bd_yes_{st.session_state.form_id}", use_container_width=True):
            st.session_state.bd_choice = "Áno"
            st.experimental_rerun()
    with c2:
        if st.button("Nie", key=f"bd_no_{st.session_state.form_id}", use_container_width=True):
            st.session_state.bd_choice = "Nie"
            st.session_state.bd_type_val = ""
            go_to("counts")
            st.experimental_rerun()
    st.write(f"Vybrané: **{st.session_state.bd_choice}**")
    if st.session_state.bd_choice == "Áno":
        st.write("Zadajte typ BD (napr. BD4) cez numerickú klávesnicu (len číslo sa použije):")
        st.text_input("", value=st.session_state.bd_type_val, key=f"display_bdtype_{st.session_state.form_id}", disabled=True)
        if st.button("Zadať typ BD", key=f"bdtype_enter_{st.session_state.form_id}", use_container_width=True):
            st.session_state.keypad_target = "bd_type_val"
            st.experimental_rerun()
        if st.session_state.keypad_target == "bd_type_val":
            render_keypad()
            if st.button("Hotovo BD", key=f"bd_done_{st.session_state.form_id}"):
                st.session_state.keypad_target = None
                go_to("counts")
                st.experimental_rerun()

def screen_counts():
    show_topbar(back_visible=True, title="4. Počty")
    st.write("Zadajte počty: počet v rade, počet radov a voľné krabice.")
    # three fields using keypad
    for label, target in [("Počet v rade", "pocet_v_rade_val"),
                          ("Počet radov", "pocet_radov_val"),
                          ("Počet voľných", "pocet_volnych_val")]:
        st.markdown(f"**{label}**")
        st.text_input("", value=st.session_state.get(target, ""), key=f"display_{target}_{st.session_state.form_id}", disabled=True)
        if st.button(f"Zadať {label}", key=f"enter_{target}_{st.session_state.form_id}", use_container_width=True):
            st.session_state.keypad_target = target
            st.experimental_rerun()
        if st.session_state.keypad_target == target:
            render_keypad()
            if st.button("Hotovo", key=f"{target}_done_{st.session_state.form_id}"):
                st.session_state.keypad_target = None
                st.experimental_rerun()
    # next
    if st.button("Pokračovať na kontrolu", key=f"to_summary_{st.session_state.form_id}", use_container_width=True):
        go_to("summary")
        st.experimental_rerun()

def screen_summary():
    show_topbar(back_visible=True, title="5. Kontrola a uloženie")
    st.write("Skontrolujte údaje pred uložením:")
    st.write(f"- Paleta: **{st.session_state.paleta_val or ('(naskenované)' if st.session_state.paleta_image else '')}**")
    if st.session_state.paleta_image:
        st.image(st.session_state.paleta_image, width=200)
    st.write(f"- Kontrolor: **{st.session_state.kontrolor_val}**")
    if st.session_state.kontrolor_image:
        st.image(st.session_state.kontrolor_image, width=200)
    st.write(f"- BD: **{st.session_state.bd_choice}**")
    if st.session_state.bd_choice == "Áno":
        st.write(f"- Typ BD: **{st.session_state.bd_type_val}**")
    st.write(f"- Počet v rade: **{st.session_state.pocet_v_rade_val}**, počet radov: **{st.session_state.pocet_radov_val}**, voľné: **{st.session_state.pocet_volnych_val}**")
    # calc total
    try:
        p_v_r = int(st.session_state.pocet_v_rade_val or 0)
        p_rad = int(st.session_state.pocet_radov_val or 0)
        p_vol = int(st.session_state.pocet_volnych_val or 0)
        pocet_krabic = p_v_r * p_rad + p_vol
        multiplier = 1
        if st.session_state.bd_choice == "Áno" and st.session_state.bd_type_val:
            try:
                multiplier = int(''.join(filter(str.isdigit, st.session_state.bd_type_val)) or "1")
            except:
                multiplier = 1
        total_units = pocet_krabic * multiplier
    except:
        total_units = "(chyba vstupu)"
    st.markdown(f"**Celkový počet jednotiek:** {total_units}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Uložiť do databázy", key=f"save_final_{st.session_state.form_id}", use_container_width=True):
            # save
            try:
                data = {
                    "paleta_id": st.session_state.paleta_val or "(skener)",
                    "pocet_v_rade": p_v_r,
                    "pocet_radov": p_rad,
                    "pocet_volnych": p_vol,
                    "typ_balika": st.session_state.bd_type_val if st.session_state.bd_choice == "Áno" else None,
                    "pocet_krabic": pocet_krabic,
                    "celkovy_pocet_jednotiek": total_units,
                    "kontrolor": st.session_state.kontrolor_val or st.session_state.kontrolor,
                    "datum": datetime.now().isoformat()
                }
                db.table("palety").insert(data).execute()
                db.table("palety_log").insert({
                    "paleta_id": data["paleta_id"],
                    "akcia": f"Uložená paleta {data['paleta_id']}",
                    "kontrolor": data["kontrolor"],
                    "datum": data["datum"]
                }).execute()
                st.success("Údaje uložené.")
                # clear and return home, but keep kontrolor logged in
                clear_form()
            except Exception as e:
                st.error(f"Chyba pri ukladaní: {e}")
    with c2:
        if st.button("Späť upraviť", key=f"back_edit_{st.session_state.form_id}", use_container_width=True):
            go_to("counts")
            st.experimental_rerun()

# ---------- ROUTER ----------
def router():
    s = st.session_state.screen
    if s == "home":
        screen_home()
    elif s == "paleta":
        screen_paleta()
    elif s == "kontrolor":
        screen_kontrolor()
    elif s == "bd":
        screen_bd()
    elif s == "counts":
        screen_counts()
    elif s == "summary":
        screen_summary()
    else:
        screen_home()

router()
