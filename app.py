import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import random
import json

# Load Firebase credentials from Streamlit secrets
firebase_json = json.loads(st.secrets["firebase_json"])
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_json)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

# Character-role pairs (name, points)
CHARACTERS = [
    ("Rama", 1000),
    ("Sita", 0),
    ("Lakshmana", 900),
    ("Bharata", 800),
    ("Shatrughna", 700),
    ("Hanuman", 600)
]

st.title("🎭 Guess Who is Sita - Multiplayer Game")

# Player name input
name = st.text_input("Enter your name to join:")

# Join game
if name:
    player_doc = db.collection("players").document(name).get()
    if not player_doc.exists:
        db.collection("players").document(name).set({
            "character": None,
            "score": 0
        })
        st.success(f"{name} joined the game!")

# Get all players
players_ref = db.collection("players")
players = list(players_ref.stream())
player_names = [p.id for p in players]

# Display players
st.write("### 👥 Current Players:")
st.write(player_names)

# Assign characters
if st.button("🎲 Assign Characters") and len(player_names) >= 4:
    available_roles = CHARACTERS[:len(player_names)]
    random.shuffle(available_roles)
    for player, role in zip(player_names, available_roles):
        players_ref.document(player).update({"character": role[0]})
    db.collection("game_state").document("round").set({"active": True})
    st.success("✅ Characters assigned. Rama can now guess who Sita is!")

# Show personal role
if name in player_names:
    my_data = players_ref.document(name).get().to_dict()
    if my_data and my_data.get("character"):
        st.info(f"🕵️ Your character is: **{my_data['character']}**")

# Get roles for all players
roles_map = {p.id: players_ref.document(p.id).get().to_dict().get("character") for p in players}
rama = next((p for p, c in roles_map.items() if c == "Rama"), None)
sita = next((p for p, c in roles_map.items() if c == "Sita"), None)

# Rama's guess
round_doc = db.collection("game_state").document("round").get()
if name == rama and round_doc.exists and sita:
    guess = st.selectbox("🧐 Who do you think is Sita?", [p for p in player_names if p != name])
    if st.button("🔍 Submit Guess"):
        if guess == sita:
            st.success("🎉 Correct! Rama gets 1000 points.")
            players_ref.document(rama).update({
                "score": firestore.Increment(1000)
            })
        else:
            st.error(f"❌ Wrong! {sita} was Sita. She gets 1000 points.")
            players_ref.document(sita).update({
                "score": firestore.Increment(1000)
            })
        db.collection("game_state").document("round").delete()

# Scoreboard
st.write("### 🧾 Scores")
for player in players_ref.stream():
    d = player.to_dict()
    st.write(f"**{player.id}**: {d.get('score', 0)} points")

# Reset game
if st.button("🔄 Reset Game"):
    for p in players_ref.stream():
        players_ref.document(p.id).delete()
    db.collection("game_state").document("round").delete()
    st.success("Game reset. Players can rejoin.")
