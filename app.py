import streamlit as st
import speech_recognition as sr
import re
import io

st.set_page_config(page_title="Voice Shopping Assistant", page_icon="🛒", layout="centered")

if "shopping_list" not in st.session_state:
    st.session_state.shopping_list = []

item_database = {
    "milk": {"category": "Dairy", "substitute": "almond milk", "price": 4},
    "apples": {"category": "Produce", "substitute": "pears", "price": 2},
    "bread": {"category": "Bakery", "substitute": "tortillas", "price": 3},
    "toothpaste": {"category": "Personal Care", "substitute": "baking soda", "price": 6},
    "water": {"category": "Beverages", "substitute": "sparkling water", "price": 1}
}
seasonal_items = ["mangoes", "watermelon"]
purchase_history = ["bread", "milk"]

language_map = {
    "English (US)": "en-US",
    "Spanish": "es-ES",
    "Hindi": "hi-IN",
    "French": "fr-FR"
}


def process_command(text):
    text = text.lower()
    feedback = "Command not entirely understood."

    if re.search(r'\b(add|buy|need)\b', text):
        match = re.search(r'(?:add|buy|need)\s+(?:some\s+|a\s+)?(\d+)?\s*(?:bottles of\s+|boxes of\s+)?([a-z\s]+)',
                          text)
        if match:
            qty = match.group(1) if match.group(1) else "1"
            item_name = match.group(2).strip()
            cat = item_database.get(item_name, {}).get("category", "General")
            st.session_state.shopping_list.append({"name": item_name, "quantity": qty, "category": cat})
            feedback = f"Added {qty} {item_name} to {cat}."

    elif re.search(r'\b(remove|delete)\b', text):
        match = re.search(r'(?:remove|delete)\s+([a-z\s]+)', text)
        if match:
            item_name = match.group(1).strip()
            initial_length = len(st.session_state.shopping_list)
            st.session_state.shopping_list = [item for item in st.session_state.shopping_list if
                                              item["name"] != item_name]
            if len(st.session_state.shopping_list) < initial_length:
                feedback = f"Removed {item_name}."
            else:
                feedback = f"Could not find {item_name}."

    elif "suggest" in text or "recommend" in text:
        missing = [item for item in purchase_history if
                   not any(i["name"] == item for i in st.session_state.shopping_list)]
        suggestions = missing + seasonal_items
        feedback = f"You might need: {', '.join(suggestions)}."

    elif "substitute" in text or "alternative" in text:
        match = re.search(r'(?:substitute|alternative)\s+(?:for\s+)?([a-z\s]+)', text)
        if match:
            item_name = match.group(1).strip()
            sub = item_database.get(item_name, {}).get("substitute", "unknown")
            feedback = f"Alternative for {item_name} is {sub}."

    elif "under" in text or "less than" in text:
        match = re.search(r'(?:under|less than)\s*(?:[\$\€\£])?(\d+)', text)
        if match:
            limit = int(match.group(1))
            found = [k for k, v in item_database.items() if v.get("price", 999) < limit]
            feedback = f"Items under ${limit}: {', '.join(found)}" if found else "No items found."

    elif "find" in text or "search" in text:
        match = re.search(r'(?:find|search)\s+(?:for\s+)?([a-z\s]+)', text)
        if match:
            target = match.group(1).strip()
            found = [i["name"] for i in st.session_state.shopping_list if target in i["name"]]
            feedback = f"Found: {', '.join(found)}" if found else "Item not in list."

    elif "clear" in text:
        st.session_state.shopping_list.clear()
        feedback = "List cleared."

    return feedback


st.title("Voice Shopping Assistant")

selected_lang_label = st.selectbox("Language", list(language_map.keys()))
selected_lang_code = language_map[selected_lang_label]

audio_value = st.audio_input("Record voice command")

if audio_value:
    recognizer = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_value.read())
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data, language=selected_lang_code)
            st.info(f'Heard: "{transcript}"')
            with st.spinner("Processing command..."):
                response_msg = process_command(transcript)
                st.success(response_msg)
    except sr.UnknownValueError:
        st.error("Could not understand audio. Please try again.")
    except sr.RequestError:
        st.error("Speech recognition service unavailable.")

st.divider()
st.subheader("Current Shopping List")

if not st.session_state.shopping_list:
    st.write("Your shopping list is empty.")
else:
    categories = sorted(list(set(item["category"] for item in st.session_state.shopping_list)))
    for cat in categories:
        st.markdown(f"**{cat}**")
        cat_items = [item for item in st.session_state.shopping_list if item["category"] == cat]
        for item in cat_items:
            st.write(f"- {item['quantity']}x {item['name']}")