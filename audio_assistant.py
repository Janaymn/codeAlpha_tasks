import speech_recognition as sr
import sys
import time
import os
import tempfile
from dotenv import load_dotenv

import laptop_tools
from groq_engine import GroqAIEngine

# Force load .env overriding any old terminal variables
load_dotenv(override=True)

# Initialize pygame mixer for gTTS audio playback
pygame_available = False
try:
    import pygame
    pygame.mixer.init()
    pygame_available = True
except Exception as e:
    print(f"[Pygame Init Warning]: {e}")

# Fallback SAPI5 / pyttsx3
sapi_speaker = None
try:
    import win32com.client
    sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
    voices = sapi_speaker.GetVoices()
    if len(voices) > 1:
        sapi_speaker.Voice = voices[1]  # Microsoft Zira Female Voice
except Exception:
    pass

def speak_gtts(text: str) -> bool:
    """Uses Google TTS for natural Arabic female speech."""
    try:
        from gtts import gTTS
        # Detect language (Arabic vs English)
        lang = 'ar' if any('\u0600' <= char <= '\u06FF' for char in text) else 'en'
        tts = gTTS(text=text, lang=lang, slow=False)
        temp_file = os.path.join(tempfile.gettempdir(), f"voice_speech_{int(time.time() * 1000)}.mp3")
        tts.save(temp_file)
        
        if pygame_available:
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            try:
                os.remove(temp_file)
            except Exception:
                pass
            return True
    except Exception as e:
        print(f"[gTTS Warning]: {e}")
    return False

def talk(text: str):
    """Speaks text out loud using female TTS voice and prints output."""
    if not text or not text.strip():
        return
        
    try:
        print(f"\n🤖 Assistant: {text}\n")
    except Exception:
        sys.stdout.buffer.write(f"\n🤖 Assistant: {text}\n".encode('utf-8'))
    
    # Primary: Natural gTTS Female Voice
    if speak_gtts(text):
        return

    # Secondary Fallback: Windows SAPI5 Speaker
    if sapi_speaker:
        try:
            sapi_speaker.Speak(text)
            return
        except Exception as e:
            print(f"[SAPI5 Audio Error]: {e}")

# Global Speech Recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8

def normalize_speech_text(text: str) -> str:
    """Cleans up phonetic mishearings for apps like Antigravity IDE & VS Code."""
    if not text or not text.strip():
        return ""
    t_lower = text.lower()
    
    # Antigravity IDE replacements
    if any(w in t_lower for w in ["antigravity", "anti gravity", "انتي جرافيتي", "انتيجرافيتي", "انتي غرافيتي", "انتيجرأفيتي", "انتي جرافي", "انتي جرافيت"]):
        if "antigravity ide" not in t_lower:
            text += " Antigravity IDE"

    # VS Code replacements
    if any(w in t_lower for w in ["vs code", "vscode", "في اس كود", "في اس", "فيجوال ستوديو", "فيجوال ستوديو كود", "فيجول كود"]):
        if "vs code" not in t_lower:
            text += " VS Code"
            
    return text

def listen(language="ar-EG") -> str:
    """
    Listens quietly and responsively for microphone input.
    """
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return ""

    try:
        command = recognizer.recognize_google(audio, language=language)
        command = normalize_speech_text(command)
        if command and command.strip():
            print(f"🎙️ You: {command}")
        return command
    except sr.UnknownValueError:
        try:
            command = recognizer.recognize_google(audio, language="en-US")
            command = normalize_speech_text(command)
            if command and command.strip():
                print(f"🎙️ You: {command}")
            return command
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
    except sr.RequestError:
        return ""

def main():
    print("=" * 65)
    print("      EGYPTIAN AI VOICE ASSISTANT (Powered by Groq LLM)     ")
    print("=" * 65)
    print("Listening... Speak into your microphone!\n")
    
    ai_engine = GroqAIEngine()
    
    # Greeting spoken out loud by Assistant
    talk("أهلاً بيك! أنا المساعد الذكي بتاعك. اؤمرني، اقدر أساعدك في إيه النهاردة؟")

    while True:
        try:
            user_speech = listen()
            
            if not user_speech:
                continue
                
            user_speech_lower = user_speech.lower()
            
            # Natural program exit phrases (Arabic & English)
            exit_phrases = ["exit", "quit", "goodbye", "bye", "مع السلامة", "اشوفك على خير", "أشوفك على خير", "اقفلي البرنامج", "قفلي البرنامج", "كفاية كدا", "كفاية كده", "شكرا كدا", "تصبح على خير"]
            if any(cmd in user_speech_lower for cmd in exit_phrases):
                talk("مع السلامة! أشوفك على خير إن شاء الله.")
                break

            # Send prompt to Groq LLM model & get model's self-generated reply
            reply = ai_engine.chat(user_speech, listen_func=listen, talk_func=talk)
            
            if reply:
                talk(reply)

        except KeyboardInterrupt:
            print("\nProgram stopped.")
            break
        except Exception as e:
            print(f"[Error]: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
