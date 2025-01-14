import tkinter as tk
import pyttsx3
import speech_recognition as sr
import datetime
import threading
import spacy
import requests
from geopy.geocoders import Nominatim
from playsound import playsound
import time
import re

from weather import check_weather
from weather import get_date 

from alarm import set_alarm
from alarm import cancel_alarm
from alarm import edit_alarm

from event import set_event
from event import cancel_event
from event import edit_event
from weather import wish_me

nlp = spacy.load("en_core_web_sm")

engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('voice', engine.getProperty('voices')[1].id)

is_listening = False
active_word = 'computer'

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    listener = sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening...')
        listener.pause_threshold = 1
        input_speech = listener.listen(source, 0, 5)
        try:
            print('Recognizing...')
            query = listener.recognize_google(input_speech, language='en-in')
            print('Input speech was:', query)
        except Exception as e:
            print("Error:", e)
            return "None"
    return query.lower()
def extract_details(command):
    doc = nlp(command)
    intent = None
    location = None
    action = None
    name = None
    time = None
    event_name = None
    event_date = None
    event_time = None

    # Extract intent (weather, date, time)
    if "weather" in command or "going out" in command:
        intent = "weather"
    elif "date" in command:
        intent = "date"
    elif "time" in command:
        intent = "time"

    # Extract location for weather
    for ent in doc.ents:
        if ent.label_ == "GPE":
            location = ent.text

    # Extract action and alarm details
    if "set" in command:
        action = "set"
    elif "edit" in command or "change" in command:
        action = "edit"
    elif "cancel" in command or "remove" in command:
        action = "cancel"

    time_match = re.search(r"(\d{1,2}:\d{2}\s*(AM|PM|am|pm|a.m.|p.m.))", command)
    if time_match:
        time = time_match.group(0).replace('.', '').strip()

    name_match = re.search(r"name\s*(to|is)?\s*([a-zA-Z0-9]+)", command)
    if name_match:
        name = name_match.group(2).strip()

#-----------------------------------------------------------------------------voice command
def process_command():
    global is_listening
    wish_me()
    while is_listening:
        command = listen()  # Listen for a voice command
        if active_word in command:
            intent, location, action, name, time, event_name, event_date, event_time = extract_details(command)

            # Handle events
            if "set event" in command or ("set" in command and "event" in command):
                if event_name and event_date and event_time:
                    set_event(event_name, event_date, event_time)
                else:
                    speak("Please provide the event name, date, and time.")
                    event_details = listen()
                    event_name, event_date, event_time = extract_details(event_details)
                    if event_name and event_date and event_time:
                        set_event(event_name, event_date, event_time)
                    else:
                        update_response("I couldn't understand the event details. Please try again.")
                        speak("I couldn't understand the event details. Please try again.")

            elif "edit event" in command:
                if event_name and event_date and event_time:
                    edit_event(event_name, event_date, event_time)
                else:
                    speak("Please provide the event name, new date, and time.")
                    event_details = listen()
                    event_name, new_event_date, new_event_time = extract_details(event_details)
                    if event_name and new_event_date and new_event_time:
                        edit_event(event_name, new_event_date, new_event_time)
                    else:
                        update_response("I couldn't understand the new event details. Please try again.")
                        speak("I couldn't understand the new event details. Please try again.")

            elif "cancel event" in command:
                if event_name:
                    cancel_event(event_name)
                else:
                    speak("Please provide the event name to cancel.")
                    
                    event_name = listen()
                    if event_name:
                        cancel_event(event_name)
                    else:
                        update_response("I couldn't understand the event name. Please try again.")
                        speak("I couldn't understand the event name. Please try again.")

            elif action == "set" and name and time:  
                set_alarm(name, time)

            elif action == "edit" and name and time:  
                edit_alarm(name, time)

            elif action == "cancel" and name:  
                cancel_alarm(name)

            elif intent == "weather":  
                if location:
                    check_weather(location)
                else:
                    speak("Please tell me the location or say 'current location' for local weather.")
                    location_input = listen()
                    if "current location" in location_input:
                        check_weather()
                    else:
                        check_weather(location_input)

            elif intent == "date":  
                get_date()

            elif intent == "time":  
                now = datetime.datetime.now().strftime("%H:%M")
                response = f"The current time is {now}."
                update_response(response)
                speak(response)

            elif "stop" in command:  
                update_response("Stopping the assistant.")
                speak("Stopping the assistant.")
                is_listening = False

            else:
                update_response("I didn't understand that command. Please try again.")
                speak("I didn't understand that command. Please try again.")

#-------------------------------------------------------------------------------------------GUI setting
def start_listening():
    global is_listening
    is_listening = True
    update_response("Voice assistant started. Listening for commands...")
    threading.Thread(target=process_command).start()

def stop_listening():
    global is_listening
    is_listening = False
    update_response("Voice assistant stopped.")
    speak("Voice assistant stopped.")

def update_response(text):
    response_label.config(text=text)

root = tk.Tk()
root.title("Voice Assistant")
root.geometry("400x300")
root.configure(bg="#E6E6FA")

frame = tk.Frame(root, bg="#E6E6FA", bd=10, relief="flat")
frame.pack(pady=20)

response_label = tk.Label(frame, text="Welcome to your Voice Assistant!", font=("Arial", 12, "bold"), wraplength=350, justify="center", bg="#E6E6FA", fg="#800080")
response_label.pack(pady=10)

start_button = tk.Button(frame, text="Start Listening", command=start_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
start_button.pack(pady=5)

stop_button = tk.Button(frame, text="Stop Listening", command=stop_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
stop_button.pack(pady=5)

footer_label = tk.Label(root, text="© 2024 HT", font=("Arial", 10), bg="#E6E6FA", fg="#800080")
footer_label.pack(side="bottom", pady=10)

root.mainloop()
