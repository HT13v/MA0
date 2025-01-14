import threading
import datetime
import time
from playsound import playsound
import pyttsx3
import re
import tkinter as tk
import spacy
import speech_recognition as sr

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
        input_speech = listener.listen(source, 0, 8)
        try:
            print('Recognizing...')
            query = listener.recognize_google(input_speech, language='en-in')
            print('Input speech was:', query)
        except Exception as e:
            print("Error:", e)
            return "None"
    return query.lower()


def parse_date_time(date_str, time_str):
    try:
        event_date = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
        event_time = parse_time(time_str)
        if not event_time:
            return None
        return datetime.datetime.combine(event_date, datetime.time(event_time[0], event_time[1]))
    except ValueError:
        return None

def parse_time(time_str):
    match = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?$", time_str, re.IGNORECASE)
    if not match:
        return None
    hour, minute, period = match.groups()
    hour, minute = int(hour), int(minute)
    if period and period.upper() == "PM" and hour != 12:
        hour += 12
    if period and period.upper() == "AM" and hour == 12:
        hour = 0
    return hour, minute

def set_event(name, date_str, time_str):
    global events
    event_datetime = parse_date_time(date_str, time_str)
    if not event_datetime:
        update_response("Invalid date or time format. Use DD-MM-YYYY for date and HH:MM AM/PM for time.")
        return
    if name in events:
        update_response(f"Event '{name}' already exists. Use edit to modify it.")
        return
    events[name] = {"datetime": event_datetime, "active": True}
    update_response(f"Event '{name}' set for {event_datetime.strftime('%d-%m-%Y %I:%M %p')}.")
    speak(f"Event '{name}' set for {event_datetime.strftime('%d-%m-%Y %I:%M %p')}.")
    threading.Thread(target=check_event_notifications, args=(name,)).start()

def edit_event(name, new_date_str, new_time_str):
    global events
    if name not in events:
        update_response(f"No event found with the name '{name}'.")
        return
    new_datetime = parse_date_time(new_date_str, new_time_str)
    if not new_datetime:
        update_response("Invalid date or time format. Use DD-MM-YYYY for date and HH:MM AM/PM for time.")
        return
    events[name]["datetime"] = new_datetime
    update_response(f"Event '{name}' updated to {new_datetime.strftime('%d-%m-%Y %I:%M %p')}.")
    speak(f"Event '{name}' updated to {new_datetime.strftime('%d-%m-%Y %I:%M %p')}.")

def cancel_event(name):
    global events
    if name not in events:
        update_response(f"No event found with the name '{name}'.")
        return
    events[name]["active"] = False
    update_response(f"Event '{name}' canceled.")
    speak(f"Event '{name}' canceled.")


def check_event_notifications(name):
    global events
    while events.get(name, {}).get("active"):
        now = datetime.datetime.now()
        event_datetime = events[name]["datetime"]

        if now.date() == event_datetime.date() and now.hour == 0 and now.minute == 0:
            update_response(f"Reminder: Event '{name}' is scheduled for today at {event_datetime.strftime('%I:%M %p')}.")
            speak(f"Reminder: Event '{name}' is scheduled for today at {event_datetime.strftime('%I:%M %p')}.")

        one_hour_before = event_datetime - datetime.timedelta(hours=1)
        if now >= one_hour_before and now < event_datetime:
            update_response(f"Reminder: Event '{name}' starts in 1 hour.")
            speak(f"Reminder: Event '{name}' starts in 1 hour.")
            break

        if now >= event_datetime:
            update_response(f"Event '{name}' has started!")
            speak(f"Event '{name}' has started!")
            break

        time.sleep(30)  
def extract_event_details(command):
    doc = nlp(command)
    event_name = None
    event_date = None
    event_time = None

    # Extract event name (noun phrases)
    for chunk in doc.noun_chunks:
        if event_name is None:
            event_name = chunk.text

    # Extract date and time
    for ent in doc.ents:
        if ent.label_ == "DATE":
            event_date = ent.text
        elif ent.label_ == "TIME":
            event_time = ent.text

    return event_name, event_date, event_time

def process_command():
    speak("Listening for your command.")
    command = listen()

    if "set event" in command:
        speak("Please provide the event name, date, and time.")
        event_details = listen()
        event_name, event_date, event_time = extract_event_details(event_details)

        if event_name and event_date and event_time:
            set_event(event_name, event_date, event_time)
        else:
            update_response("I couldn't understand the event details. Please try again.")
            speak("I couldn't understand the event details. Please try again.")

    elif "edit event" in command:
        speak("Please provide the event name, new date, and time.")
        event_details = listen()
        event_name, new_event_date, new_event_time = extract_event_details(event_details)

        if event_name and new_event_date and new_event_time:
            edit_event(event_name, new_event_date, new_event_time)
        else:
            update_response("I couldn't understand the new event details. Please try again.")
            speak("I couldn't understand the new event details. Please try again.")

    elif "cancel event" in command:
        speak("Please provide the event name to cancel.")
        event_name = listen()

        if event_name:
            cancel_event(event_name)
        else:
            update_response("I couldn't understand the event name. Please try again.")
            speak("I couldn't understand the event name. Please try again.")
    else:
        update_response("I didn't understand your command. Please try again.")
        speak("I didn't understand your command. Please try again.")

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

response_label = tk.Label(frame, text="Welcome to your Voice Assistant!", font=("Arial", 12, "bold"), wraplength=350, justify="center", bg="#E6E6FA", fg="#800080")  # Purple text
response_label.pack(pady=10)

start_button = tk.Button(frame, text="Start Listening", command=start_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
start_button.pack(pady=5)

stop_button = tk.Button(frame, text="Stop Listening", command=stop_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
stop_button.pack(pady=5)

footer_label = tk.Label(root, text="© 2024 HT", font=("Arial", 10), bg="#E6E6FA", fg="#800080")  # Purple text
footer_label.pack(side="bottom", pady=10)

root.mainloop()
