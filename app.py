import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import random
import json

# 🔐 Initialize Firebase from secrets (for Streamlit Cloud)
firebase_json = json.loads(st.secrets["firebase_json"])
cred = credentials.Certificate(firebase_json)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Character roles and points
CHARACTERS = [
    ("Rama", 1000),
    ("Sita", 0),
    ("Lakshmana", 900),
    ("Bharata", 800),
    ("Shatrughna", 700),
    ("Hanuman", 600)
]

st.title("🎭 Guess Who is Sita - Multiplayer Game")

# Player joins
name = st.text_input("Enter your name to join:")
if name:
    doc = db.collection("players").document(name).get()
    if not doc.exists:
        db.collection("players").document(name).set({
            "character": None,
            "score": 0
        })
        st.success(f"{name} joined!")

# Show list of players
players = list(db.collection("players").stream())
player_names = [p.id for p in players]
st.write("### 👥 Players Joined:", player_names)

# Assign characters
if st.button("🎲 Assign Characters") and len(player_names) >= 4:
    roles = CHARACTERS[:len(player_names)]
    random.shuffle(roles)
    for player, role in zip(player_names, roles):
        db.collection("players").document(player).update({"character": role[0]})
    db.collection("game_state").document("round").set({"active": True})
    st.success("✅ Characters assigned! Rama can now guess who Sita is.")

# Show your role
if name in player_names:
    my_doc = db.collection("players").document(name).get()
    my_data = my_doc.to_dict()
    if my_data and my_data.get("character"):
        st.write(f"🕵️ Your character is: **{my_data['character']}**")

# Rama guesses Sita
player_roles = {
    p.id: db.collection("players").document(p.id).get().to_dict().get("character")
    for p in players
}
rama = next((p for p, c in player_roles.items() if c == "Rama"), None)
sita = next((p for p, c in player_roles.items() if c == "Sita"), None)

if name == rama and rama and sita:
    guess = st.selectbox("🧐 Who do you think is Sita?", [p for p in player_names if p != name])
    if st.button("🔍 Submit Guess"):
        if guess == sita:
            st.success("🎉 Correct guess! Rama gets 1000 points.")
            db.collection("players").document(rama).update({
                "score": firestore.Increment(1000)
            })
        else:
            st.error(f"❌ Wrong! {sita} was Sita. Sita gets 1000 points.")
            db.collection("players").document(sita).update({
                "score": firestore.Increment(1000)
            })
        # End the round
        db.collection("game_state").document("round").delete()

# Show scores
st.write("### 🧾 Scores")
for p in db.collection("players").stream():
    d = p.to_dict()
    st.write(f"**{p.id}**: {d.get('score', 0)} points")

# Reset game
if st.button("🔄 Reset Game"):
    for p in db.collection("players").stream():
        db.collection("players").document(p.id).delete()
    db.collection("game_state").document("round").delete()
    st.success("Game reset. All data cleared.")
