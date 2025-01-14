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
alarms = {}
events = {}

nlp = spacy.load("en_core_web_sm")

engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('voice', engine.getProperty('voices')[1].id)


def speak(text):
    engine.say(text)
    engine.runAndWait()



def listen():
    listener = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print('Listening...')
            listener.pause_threshold = 1
            input_speech = listener.listen(source, timeout=5)
            print('Recognizing...')
            query = listener.recognize_google(input_speech, language='en-in')
            print('Input speech was:', query)
            return query
        except sr.WaitTimeoutError:
            return "Timeout occurred while listening."
        except sr.UnknownValueError:
            return "I didn't catch that. Could you repeat?"
        except Exception as e:
            print("Error:", e)
            return "An error occurred while listening."



def get_date():
    now = datetime.datetime.now()
    month_name = now.month
    day_name = now.day
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ordinal_names = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th', '21st', '22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th', '31st']
    response = f"Today is {month_names[month_name - 1]} {ordinal_names[day_name - 1]}."
    update_response(response)
    speak(response)
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
def wish_me():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")
    speak("How can I assist you today?")
#---------------------------------------------------------------------------------------------weather extract
def extract_weather_details(command):
    doc = nlp(command)
    intent = None
    location = None
    if "weather" in command or "going out" in command:
        intent = "weather"
    elif "date" in command:
        intent = "date"
    elif "time" in command:
        intent = "time"
    for ent in doc.ents:
        if ent.label_ == "GPE":
            location = ent.text
            break
    return intent, location

def check_weather(location=None):
    api_key = '3cd49b4e185c894d459bfde11d916db0'
    geolocator = Nominatim(user_agent="geoapiExercises")
    if not location:
        location_data = requests.get("http://ip-api.com/json").json()
        city = location_data.get("city", "Unknown Location")
    else:
        city = location
    try:
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        weather_data = requests.get(weather_url).json()
        if weather_data.get("weather"):
            weather_condition = weather_data["weather"][0]["description"]
            temperature = weather_data["main"]["temp"]
            if "rain" in weather_condition:
                response = f"The weather in {city} is {weather_condition} with a temperature of {temperature}°C. You might want to bring an umbrella."
            elif "storm" in weather_condition:
                response = f"The weather in {city} is {weather_condition} with a temperature of {temperature}°C. It's stormy, so it's safer to stay home."
            else:
                response = f"The weather in {city} is {weather_condition} with a temperature of {temperature}°C. Have a nice day!"
        else:
            response = f"Sorry, I couldn't retrieve the weather for {city}."
        update_response(response)
        speak(response)
    except Exception as e:
        print("Error:", e)
        update_response("Sorry, I couldn't retrieve the weather data.")
        speak("Sorry, I couldn't retrieve the weather data.")
#--------------------------------------------------------------------------------------------alarm
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

#--------------------------------------------------------------------------------event

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
            playsound("alarm.wav")
            speak(f"Reminder: Event '{name}' is scheduled for today at {event_datetime.strftime('%I:%M %p')}.")

        one_hour_before = event_datetime - datetime.timedelta(hours=1)
        if now >= one_hour_before and now < event_datetime:
            update_response(f"Reminder: Event '{name}' starts in 1 hour.")
            playsound("alarm.wav")
            speak(f"Reminder: Event '{name}' starts in 1 hour.")
            break

        if now >= event_datetime:
            update_response(f"Event '{name}' has started!")
            playsound("alarm.wav")
            speak(f"Event '{name}' has started!")
            break
        if now >= event_datetime - datetime.timedelta(hours=1) and now < event_datetime:
            if not events[name].get("one_hour_notified"):
                update_response(f"Reminder: Event '{name}' starts in 1 hour.")
                playsound("alarm.wav")
                speak(f"Reminder: Event '{name}' starts in 1 hour.")
                events[name]["one_hour_notified"] = True
            
        time.sleep(30)  
def extract_event_details(command):
    doc = nlp(command)
    event_name = None
    event_date = None
    event_time = None

    for chunk in doc.noun_chunks:
        if event_name is None:
            event_name = chunk.text

    for ent in doc.ents:
        if ent.label_ == "DATE":
            event_date = ent.text
        elif ent.label_ == "TIME":
            event_time = ent.text

    return event_name, event_date, event_time

is_listening = False
active_word = 'computer'
#-----------------------------------------------------------------------------voice command
def process_command():
    global is_listening
    wish_me()  
    while is_listening:
        command = listen()  #-------------------------------------Listen for a voice command
        if active_word in command:
            #--------------------------------------------------------------- Extract intents
            intent, location = extract_weather_details(command)
            action, name, time = extract_alarm_details(command)
            event_name, event_date, event_time = extract_event_details(command)

            # -------------------------------------------------------------------Handle commands
            if "set event" in command or ("set" in command and "event" in command):
                if event_name and event_date and event_time:
                    set_event(event_name, event_date, event_time)
                else:
                    speak("Please provide the event name, date, and time.")
                    event_details = listen()
                    event_name, event_date, event_time = extract_event_details(event_details)
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
                    event_name, new_event_date, new_event_time = extract_event_details(event_details)
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
