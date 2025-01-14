import tkinter as tk
import pyttsx3
import speech_recognition as sr
import datetime
import requests
from geopy.geocoders import Nominatim
import threading

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('voice', engine.getProperty('voices')[1].id)

# Global flag to manage listening state
is_listening = False
active_word = 'computer'
# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen and recognize voice commands
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

# Function to check the weather based on command
def check_weather(location=None):
    api_key = '3cd49b4e185c894d459bfde11d916db0'
    geolocator = Nominatim(user_agent="geoapiExercises")
    
    if not location:
        # Get current location based on IP address (approximate)
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

# Function to greet the user based on time of day
def wish_me():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")
    speak("How can I assist you today?")

def date():
    now = datetime.datetime.now()
    month_name = now.month
    day_name = now.day
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ordinal_names = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th', '21st', '22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th', '31st']
    response = f"Today is {month_names[month_name - 1]} {ordinal_names[day_name - 1]}."
    update_response(response)
    speak(response)

# Main function to handle voice commands
def process_command():
    global is_listening
    wish_me()
    while is_listening:
        command = listen()
        if active_word in command:
            if 'weather' in command:
                update_response("Please tell me the location or say 'current location' for local weather.")
                speak("Please tell me the location or say 'current location' for local weather.")
                location = listen()
                if "current location" in location:
                    check_weather()
                else:
                    check_weather(location)
            elif "date" in command:
                    update_response("")
                    date()
            elif 'stop' in command:
                update_response("Stopping the assistant.")
                speak("Stopping the assistant.")
                is_listening = False
        

# Function to start listening in a separate thread
def start_listening():
    global is_listening
    is_listening = True
    update_response("Voice assistant started. Listening for commands...")
    threading.Thread(target=process_command).start()

# Function to stop listening
def stop_listening():
    global is_listening
    is_listening = False
    update_response("Voice assistant stopped.")
    speak("Voice assistant stopped.")

# Function to update response on GUI
def update_response(text):
    response_label.config(text=text)

root = tk.Tk()
root.title("Voice Assistant")
root.geometry("400x300")
root.configure(bg="#E6E6FA")  # Light blue background

# Frame for main content
frame = tk.Frame(root, bg="#E6E6FA", bd=10, relief="flat")
frame.pack(pady=20)

# Display area for assistant responses
response_label = tk.Label(frame, text="Welcome to your Voice Assistant!", font=("Arial", 12, "bold"), wraplength=350, justify="center", bg="#E6E6FA", fg="#800080")  # Purple text
response_label.pack(pady=10)

# Start and Stop buttons
start_button = tk.Button(frame, text="Start Listening", command=start_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
start_button.pack(pady=5)

stop_button = tk.Button(frame, text="Stop Listening", command=stop_listening, width=20, bg="#E6E6FA", fg="#800080", font=("Arial", 12, "bold"))
stop_button.pack(pady=5)

# Adding a footer label
footer_label = tk.Label(root, text="© 2024 HT", font=("Arial", 10), bg="#E6E6FA", fg="#800080")  # Purple text
footer_label.pack(side="bottom", pady=10)

root.mainloop()
