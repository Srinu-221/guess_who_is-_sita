import streamlit as st
import pyrebase
import random
import time

# Firebase config
firebaseConfig = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_DOMAIN",
    "databaseURL": "YOUR_DB_URL",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_BUCKET",
    "messagingSenderId": "YOUR_SENDER_ID",
    "appId": "YOUR_APP_ID"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

CHARACTERS = [
    ("Rama", 1000),
    ("Sita", 0),
    ("Lakshmana", 900),
    ("Bharata", 800),
    ("Shatrughna", 700),
    ("Hanuman", 600)
]

st.title("🎭 Guess Who is Sita - Multiplayer Game")

# Join
player = st.text_input("Enter your name to join:")
if player:
    if not db.child("players").child(player).get().val():
        db.child("players").child(player).set({"character": None, "score": 0})
        st.success(f"{player} joined the game!")

# Show current players
players_data = db.child("players").get().val() or {}
st.write("### 👥 Current Players")
st.write(list(players_data.keys()))

# Assign roles
if st.button("🎲 Start Round") and len(players_data) >= 4:
    roles = CHARACTERS[:len(players_data)]
    random.shuffle(roles)
    for name, role in zip(players_data.keys(), roles):
        db.child("players").child(name).update({"character": role[0]})
    db.child("game_state").set({"assigned": True})
    st.success("Characters assigned!")

# Show your role
if player and player in players_data:
    my_data = db.child("players").child(player).get().val()
    if my_data.get("character"):
        st.write(f"🕵️ Your role: **{my_data['character']}**")

# Rama guesses
game_state = db.child("game_state").get().val()
if game_state and game_state.get("assigned"):
    player_roles = {name: db.child("players").child(name).get().val()['character']
                    for name in players_data}

    rama = next((k for k, v in player_roles.items() if v == "Rama"), None)
    sita = next((k for k, v in player_roles.items() if v == "Sita"), None)

    if player == rama:
        guess = st.selectbox("Who is Sita?", [p for p in players_data if p != player])
        if st.button("🔍 Submit Guess"):
            if guess == sita:
                st.success("🎉 Correct!")
                curr = db.child("players").child(rama).child("score").get().val()
                db.child("players").child(rama).update({"score": curr + 1000})
            else:
                st.error(f"❌ Wrong! It was {sita}")
                curr = db.child("players").child(sita).child("score").get().val()
                db.child("players").child(sita).update({"score": curr + 1000})
            db.child("game_state").remove()

# Show scores
st.write("### 🧾 Scores")
scores = {k: v["score"] for k, v in players_data.items()}
for name, score in scores.items():
    st.write(f"{name}: {score} pts")

# Reset game
if st.button("🔄 Reset"):
    db.child("players").remove()
    db.child("game_state").remove()
    st.success("Game reset!")
