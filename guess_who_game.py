import streamlit as st
import random

# Define roles and points
CHARACTERS = [
    ("Rama", 1000),
    ("Sita", 0),
    ("Lakshmana", 900),
    ("Bharata", 800),
    ("Shatrughna", 700),
    ("Hanuman", 600)
]

# Initialize session state
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'assigned' not in st.session_state:
    st.session_state.assigned = False
if 'current_round' not in st.session_state:
    st.session_state.current_round = 1
if 'scores' not in st.session_state:
    st.session_state.scores = {}

st.title("🎮 Guess Who is Sita - Online Multiplayer Game")

# Player joins with name
name = st.text_input("Enter your name to join:")
if name and name not in st.session_state.players:
    st.session_state.players[name] = None
    st.session_state.scores[name] = 0
    st.success(f"{name} has joined the game!")

st.write("### Current Players:")
st.write(list(st.session_state.players.keys()))

# Assign characters
if st.button("Start Round (Assign Characters)") and len(st.session_state.players) >= 4:
    selected_chars = CHARACTERS[:len(st.session_state.players)]
    random.shuffle(selected_chars)
    for player, role in zip(st.session_state.players.keys(), selected_chars):
        st.session_state.players[player] = role
    st.session_state.assigned = True
    st.success("Characters assigned. Ask Rama to guess who Sita is.")

# Display role only to the player
if name in st.session_state.players and st.session_state.assigned:
    st.write(f"Your character is: **{st.session_state.players[name][0]}**")

# Rama guessing Sita
if st.session_state.assigned and st.session_state.players.get(name, (None,))[0] == "Rama":
    guess = st.selectbox("Who do you think is Sita?", [p for p in st.session_state.players if p != name])
    if st.button("Submit Guess"):
        actual_sita = [p for p, role in st.session_state.players.items() if role[0] == "Sita"][0]
        if guess == actual_sita:
            st.success("🎉 Correct! You guessed Sita!")
            st.session_state.scores[name] += 1000
        else:
            st.error(f"❌ Wrong guess. {actual_sita} was Sita.")
            st.session_state.scores[actual_sita] += 1000
        st.session_state.assigned = False
        st.session_state.current_round += 1

# Show Scores
if st.session_state.current_round > 1:
    st.write("### 🧾 Current Scores:")
    for player, score in st.session_state.scores.items():
        st.write(f"{player}: {score} points")

# Reset Game
if st.button("🔄 Reset Game"):
    st.session_state.players = {}
    st.session_state.scores = {}
    st.session_state.assigned = False
    st.session_state.current_round = 1
    st.success("Game reset successfully.")
