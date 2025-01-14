from playsound import playsound
import time
import re
import tkinter as tk
import pyttsx3
import speech_recognition as sr
import datetime
import threading
import spacy


nlp = spacy.load("en_core_web_sm")

engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('voice', engine.getProperty('voices')[1].id)


alarms = {}
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


def parse_time(time_str):
    match = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", time_str, re.IGNORECASE)
    if not match:
        return None
    hour, minute, period = match.groups()
    hour, minute = int(hour), int(minute)
    if period and period.upper() == "PM" and hour != 12:
        hour += 12
    if period and period.upper() == "AM" and hour == 12:
        hour = 0
    return hour, minute

def extract_alarm_details(command):
    doc = nlp(command)
    action = None
    name = None
    time = None

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

    return action, name, time

def set_alarm(name, time_str):
    global alarms
    alarm_time = parse_time(time_str)
    if not alarm_time:
        update_response("Invalid time format. Use HH:MM AM/PM.")
        return
    if name in alarms:
        update_response(f"Alarm '{name}' already exists. Use edit to modify it.")
        return
    alarms[name] = {"time": alarm_time, "active": True}
    update_response(f"Alarm '{name}' set for {time_str}.")
    speak(f"Alarm '{name}' set for {time_str}.")
    threading.Thread(target=check_alarm, args=(name,)).start()

def check_alarm(name):
    global alarms
    while alarms.get(name, {}).get("active"):
        now = datetime.datetime.now()
        alarm_time = alarms[name]["time"]
        if now.hour == alarm_time[0] and now.minute == alarm_time[1]:
            update_response(f"Alarm '{name}' is ringing!")
            speak(f"Alarm '{name}' is ringing!")
            playsound("alarm.wav")
            alarms[name]["active"] = False
            break
        time.sleep(20)


def edit_alarm(name, new_time_str):
    global alarms
    if name not in alarms:
        update_response(f"No alarm found with the name '{name}'.")
        return
    new_time = parse_time(new_time_str)
    if not new_time:
        update_response("Invalid time format. Use HH:MM AM/PM.")
        return

    alarms[name]["time"] = new_time
    alarms[name]["triggered"] = False  
    alarms[name]["active"] = True  

    update_response(f"Alarm '{name}' updated to {new_time_str}.")
    speak(f"Alarm '{name}' updated to {new_time_str}.")
    threading.Thread(target=check_alarm, args=(name,)).start()

def cancel_alarm(name):
    global alarms
    if name not in alarms:
        update_response(f"No alarm found with the name '{name}'.")
        return
    alarms[name]["active"] = False
    update_response(f"Alarm '{name}' canceled.")
    speak(f"Alarm '{name}' canceled.")

def process_command():
    global is_listening
    while is_listening:
        command = listen()
        if active_word in command:
            action, name, time = extract_alarm_details(command)

            if action == "set" and name and time:
                set_alarm(name, time)
            elif action == "edit" and name and time:
                edit_alarm(name, time)
            elif action == "cancel" and name:
                cancel_alarm(name)
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

response_label = tk.Label(frame, text="Welcome to your Voice Assistant!", font=("Arial", 12, "bold"), wraplength=350, justify="center", bg="#E6E6FA", fg="#800080")
response_label.pack(pady=10)

start_button = tk.Button(frame, text="Start Listening", command=start_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
start_button.pack(pady=5)

stop_button = tk.Button(frame, text="Stop Listening", command=stop_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
stop_button.pack(pady=5)

footer_label = tk.Label(root, text="© 2024 HT", font=("Arial", 10), bg="#E6E6FA", fg="#800080")
footer_label.pack(side="bottom", pady=10)

root.mainloop()
