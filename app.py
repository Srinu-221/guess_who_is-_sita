import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import tempfile
import random

# --- Firebase Setup (via Secrets + Temp File) ---
firebase_json_str = st.secrets["firebase_json"]
firebase_json = json.loads(firebase_json_str)

# Save JSON to a temporary file
with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
    json.dump(firebase_json, f)
    firebase_cert_path = f.name

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cert_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Game Characters and Points ---
CHARACTERS = [
    ("Rama", 1000),
    ("Sita", 0),
    ("Lakshmana", 900),
    ("Bharata", 800),
    ("Shatrughna", 700),
    ("Hanuman", 600)
]

st.title("🎭 Guess Who is Sita - Multiplayer Game")

# --- Player Join ---
name = st.text_input("Enter your name to join the game:")

if name:
    doc_ref = db.collection("players").document(name)
    if not doc_ref.get().exists:
        doc_ref.set({"character": None, "score": 0})
        st.success(f"{name} has joined the game!")

# --- Show Current Players ---
players = list(db.collection("players").stream())
player_names = [p.id for p in players]
st.write("### 👥 Current Players")
st.write(player_names)

# --- Assign Characters ---
if st.button("🎲 Assign Characters") and len(player_names) >= 4:
    roles = CHARACTERS[:len(player_names)]
    random.shuffle(roles)
    for player, role in zip(player_names, roles):
        db.collection("players").document(player).update({"character": role[0]})
    db.collection("game_state").document("round").set({"active": True})
    st.success("Characters assigned! Rama can now guess who Sita is.")

# --- Show Your Role ---
if name in player_names:
    player_doc = db.collection("players").document(name).get().to_dict()
    if player_doc and player_doc.get("character"):
        st.info(f"🕵️ Your character: **{player_doc['character']}**")

# --- Guessing Logic ---
player_roles = {
    p.id: db.collection("players").document(p.id).get().to_dict().get("character")
    for p in players
}
rama = next((n for n, c in player_roles.items() if c == "Rama"), None)
sita = next((n for n, c in player_roles.items() if c == "Sita"), None)

round_active = db.collection("game_state").document("round").get().exists

if name == rama and round_active and sita:
    guess = st.selectbox("🧐 Rama, who do you think is Sita?", [p for p in player_names if p != name])
    if st.button("🔍 Submit Guess"):
        if guess == sita:
            st.success("🎉 Correct! Rama gets 1000 points.")
            db.collection("players").document(rama).update({
                "score": firestore.Increment(1000)
            })
        else:
            st.error(f"❌ Wrong! {sita} was Sita. She gets 1000 points.")
            db.collection("players").document(sita).update({
                "score": firestore.Increment(1000)
            })
        db.collection("game_state").document("round").delete()

# --- Show Scores ---
st.write("### 🧾 Scores")
for p in db.collection("players").stream():
    data = p.to_dict()
    st.write(f"**{p.id}**: {data.get('score', 0)} points")

# --- Reset Game ---
if st.button("🔄 Reset Game"):
    for p in db.collection("players").stream():
        db.collection("players").document(p.id).delete()
    db.collection("game_state").document("round").delete()
    st.success("Game reset! Everyone can join again.")
