from gtts import gTTS
import os
import argparse
import pyttsx3

def text_to_speech(text, rate = 180):
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)
    engine.say(text)
    engine.runAndWait()

def main():
    parser = argparse.ArgumentParser(description = "Text To Speech CLI")
    parser.add_argument("text", type = str, help = "Text to convert")
    parser.add_argument("--rate", type = int, default = 180, help = "speech rate")
    args = parser.parse_args()
    text_to_speech(args.text, args.rate)

if __name__ == "__main__":
    user_input = "Hello Bharat, this is your TTS system"
    text_to_speech(user_input)