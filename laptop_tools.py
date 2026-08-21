import subprocess
import time
import os
import sys
import webbrowser
import datetime
import pytz
import pycountry
import pyautogui
import urllib.parse
import requests
import pywhatkit
import pyperclip
from googlesearch import search

def is_app_running(process_name: str) -> bool:
    """Checks if a process is already running in Windows tasklist."""
    try:
        output = subprocess.check_output('tasklist', shell=True).decode('utf-8', errors='ignore')
        return process_name.lower() in output.lower()
    except Exception:
        return False

def open_application(app_name: str, force: bool = False) -> str:
    """
    Dynamically launches or re-opens applications on the laptop based on LLM intent.
    If force=True, forces launching/re-opening even if already running.
    """
    app = app_name.lower().strip()
    try:
        if any(w in app for w in ["word", "مستند", "وورد", "وثيقة"]):
            if force or not is_app_running('winword.exe'):
                try:
                    subprocess.Popen('start winword', shell=True)
                except Exception:
                    os.system('start winword')
                return "Opened Microsoft Word"
            return "Microsoft Word is already running."
        
        elif any(w in app for w in ["notepad", "notes", "ملاحظات", "نوت باد", "مفكرة"]):
            if force or not is_app_running('notepad.exe'):
                subprocess.Popen(['notepad.exe'])
                return "Opened Notepad"
            return "Notepad is already running."
        
        elif any(w in app for w in ["calc", "calculator", "حاسبة", "آلة حاسبة", "حسابات"]):
            if force or not is_app_running('calc.exe'):
                subprocess.Popen(['calc.exe'])
                return "Opened Calculator"
            return "Calculator is already running."

        elif any(w in app for w in ["whatsapp", "واتساب", "واتس"]):
            try:
                subprocess.Popen('start whatsapp:', shell=True)
            except Exception:
                webbrowser.open("https://web.whatsapp.com")
            return "Opened WhatsApp"

        elif any(w in app for w in ["zoom", "زوم"]):
            try:
                subprocess.Popen('start zoommtg:', shell=True)
            except Exception:
                webbrowser.open("https://zoom.us")
            return "Opened Zoom"

        elif any(w in app for w in ["spotify", "سبوتيفاي"]):
            try:
                subprocess.Popen('start spotify:', shell=True)
            except Exception:
                webbrowser.open("https://open.spotify.com")
            return "Opened Spotify"

        elif any(w in app for w in ["teams", "تيمز"]):
            subprocess.Popen('start msteams:', shell=True)
            return "Opened Microsoft Teams"

        elif any(w in app for w in ["discord", "دسكورد"]):
            subprocess.Popen('start discord:', shell=True)
            return "Opened Discord"

        elif any(w in app for w in ["antigravity", "anti gravity", "انتي جرافيتي", "انتيجرافيتي", "انتي غرافيتي", "انتيجرأفيتي"]):
            antigravity_path = r'C:\Users\ayman\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe'
            if os.path.exists(antigravity_path):
                subprocess.Popen([antigravity_path])
            else:
                subprocess.Popen('start antigravity:', shell=True)
            return "Opened Antigravity IDE"

        elif any(w in app for w in ["vscode", "vs code", "code", "في اس كود", "في اس", "فيجوال ستوديو", "فيجوال ستوديو كود", "فيجول كود"]):
            try:
                subprocess.Popen('start vscode:', shell=True)
            except Exception:
                subprocess.Popen(['code.cmd'], shell=True)
            return "Opened VS Code"

        elif any(w in app for w in ["telegram", "تليجرام"]):
            subprocess.Popen('start tg:', shell=True)
            return "Opened Telegram"
        
        elif any(w in app for w in ["chrome", "browser", "متصفح", "كروم", "انترنت"]):
            try:
                subprocess.Popen(['chrome.exe'])
            except Exception:
                webbrowser.open("https://www.google.com")
            return "Opened Web Browser"
            
        elif any(w in app for w in ["explorer", "files", "folder", "ملفات", "فولدر", "فايلات"]):
            subprocess.Popen(['explorer.exe'])
            return "Opened File Explorer"
            
        elif any(w in app for w in ["cmd", "terminal", "command", "ترمنال"]):
            subprocess.Popen(['cmd.exe'])
            return "Opened Command Prompt"

        elif any(w in app for w in ["paint", "رسام", "رسم"]):
            if force or not is_app_running('mspaint.exe'):
                subprocess.Popen(['mspaint.exe'])
                return "Opened Paint"
            return "Paint is already running."
            
        else:
            try:
                subprocess.Popen(f'start {app}:', shell=True)
            except Exception:
                subprocess.Popen(f'start {app}', shell=True)
            return f"Opened {app_name}"
    except Exception as e:
        return f"Could not open {app_name}: {str(e)}"

def dictation_write(text: str):
    """
    Writes text to active window using Clipboard (supports Arabic, English, symbols).
    """
    if not text or not text.strip():
        return
    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.05)
    pyautogui.press('enter')

def is_dictation_stop_intent(text: str) -> bool:
    """Detects natural conversational completion or stopping intent in Arabic or English."""
    if not text:
        return False
    t = text.lower().strip()
    stop_phrases = [
        "خلصت", "خلاص", "تمام كدا", "تمام كده", "كفاية", "كفايه", "وقف", "وقفي", 
        "اقفلي", "قفلي", "إغلاق", "اغلاق", "أغلقي", "مفيش حاجة تاني", "مفيش حاجة تانية",
        "مش عاوزة حاجة تاني", "مش عايزة حاجة تانية", "شكرا كدا", "شكراً كدا",
        "exit", "stop", "close", "done", "finish", "finished", "goodbye", "bye", "that's all"
    ]
    return any(phrase in t for phrase in stop_phrases)

def dictate_to_notepad(listen_func, talk_func, initial_text: str = "") -> str:
    """
    Opens Notepad if not running and enters live dictation mode until natural completion.
    """
    try:
        notepad_process = None
        if not is_app_running('notepad.exe'):
            notepad_process = subprocess.Popen(['notepad.exe'])
            time.sleep(1.5)  # Wait for Notepad window to open
        else:
            time.sleep(0.5)

        pyautogui.click()  # Ensure Notepad window has active focus
        
        if initial_text and initial_text.strip():
            dictation_write(initial_text.strip())
            print(f" ✍️ Wrote initial text to Notepad: {initial_text}")
        
        talk_func("فتحت لك النوت باد.. اتفضلي إملي وأنا هكتب كل حاجة تقوليها. ولما تخلصي قوليلي إنك خلصتي!")
        time.sleep(0.5)
        
        while True:
            text = listen_func()
            if not text or text.lower() == "none" or not text.strip():
                continue
                
            if is_dictation_stop_intent(text):
                talk_func("تمام، قفلت النوت باد.")
                close_application("notepad")
                break
                
            dictation_write(text)
            print(f" ✍️ Wrote to Notepad: {text}")
            
        return "Dictation completed naturally and Notepad application has been closed."
    except Exception as e:
        return f"Error during Notepad dictation: {str(e)}"

def dictate_to_word(listen_func, talk_func, initial_text: str = "") -> str:
    """
    Opens Microsoft Word if not running and enters live dictation mode until natural completion.
    """
    try:
        if not is_app_running('winword.exe'):
            try:
                subprocess.Popen(['start', 'winword'], shell=True)
            except Exception:
                os.system('start winword')
            time.sleep(3.0)  # Wait for Word to open
            pyautogui.press('enter')  # Select blank document
            time.sleep(1.0)
        else:
            time.sleep(0.5)

        pyautogui.click()
        
        if initial_text and initial_text.strip():
            dictation_write(initial_text.strip())
            print(f" ✍️ Wrote initial text to Word: {initial_text}")

        talk_func("فتحت لك برنامج مايكروسوفت وورد.. اتفضلي إملي وأنا هكتب كل حاجة. ولما تخلصي قوليلي إنك خلصتي!")
        time.sleep(0.5)
        
        while True:
            text = listen_func()
            if not text or text.lower() == "none" or not text.strip():
                continue
                
            if is_dictation_stop_intent(text):
                talk_func("تمام، تم إنهاء الإملاء وإغلاق الـ Word.")
                close_application("word")
                break
                
            dictation_write(text)
            print(f" ✍️ Wrote to Word: {text}")
            
        return "Dictation completed naturally and Microsoft Word application has been closed."
    except Exception as e:
        return f"Error during Word dictation: {str(e)}"

def play_on_youtube(song_name: str) -> str:
    """Plays a song or video on YouTube."""
    try:
        pywhatkit.playonyt(song_name)
        return f"Playing '{song_name}' on YouTube."
    except Exception as e:
        return f"Could not play on YouTube: {str(e)}"

def open_netflix_movie(movie_name: str) -> str:
    """Searches and opens a movie or show on Netflix."""
    try:
        movie_encoded = movie_name.replace(" ", "%20")
        url = f"https://www.netflix.com/search?q={movie_encoded}"
        webbrowser.open(url)
        return f"Opening '{movie_name}' on Netflix."
    except Exception as e:
        return f"Could not open Netflix: {str(e)}"

def get_system_time(timezone_str: str = "UTC") -> str:
    """Returns current time formatted for a timezone or city."""
    try:
        tz = None
        if timezone_str:
            for t in pytz.all_timezones:
                if timezone_str.lower() in t.lower():
                    tz = pytz.timezone(t)
                    break
                    
        if not tz:
            tz = pytz.timezone("UTC")
            
        current_time = datetime.datetime.now(tz).strftime('%I:%M %p')
        return f"The time in {tz.zone} is {current_time}"
    except Exception as e:
        return f"Error fetching time: {str(e)}"

def search_google(query: str) -> str:
    """Performs a web search on Google, opens search results in web browser, and returns factual summaries."""
    if not query or not query.strip():
        return "Please specify a search query."
        
    query_clean = query.strip()
    encoded_query = urllib.parse.quote(query_clean)
    
    # 1. Open Google Search in Web Browser
    try:
        webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
    except Exception as e:
        print(f"[WebBrowser Search Warning]: {e}")

    # 2. Fetch factual summary
    search_summary = ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        api_url = f"https://ar.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
        resp = requests.get(api_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            extract = data.get('extract')
            if extract:
                search_summary = extract
                
        if not search_summary:
            api_url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
            resp_en = requests.get(api_url_en, headers=headers, timeout=5)
            if resp_en.status_code == 200:
                data_en = resp_en.json()
                extract_en = data_en.get('extract')
                if extract_en:
                    search_summary = extract_en
    except Exception as e:
        print(f"[Web Search API Warning]: {e}")

    if search_summary:
        return f"Opened Google search in browser for '{query_clean}'. Info summary: {search_summary[:300]}"
    
    return f"Opened Google search in browser for '{query_clean}'."

def close_application(app_name: str) -> str:
    """
    Closes / terminates an application on the laptop (Notepad, Word, Chrome, WhatsApp, Zoom, Calculator, etc.)
    """
    app = app_name.lower().strip()
    try:
        if any(w in app for w in ["word", "مستند", "وورد", "وثيقة"]):
            subprocess.Popen('taskkill /F /IM winword.exe', shell=True)
            return "Closed Microsoft Word"
            
        elif any(w in app for w in ["notepad", "notes", "ملاحظات", "نوت باد", "مفكرة"]):
            subprocess.Popen('taskkill /F /IM notepad.exe', shell=True)
            return "Closed Notepad"
            
        elif any(w in app for w in ["calc", "calculator", "حاسبة", "آلة حاسبة", "حسابات"]):
            subprocess.Popen('taskkill /F /IM calc.exe /IM CalculatorApp.exe', shell=True)
            return "Closed Calculator"
            
        elif any(w in app for w in ["whatsapp", "واتساب", "واتس"]):
            subprocess.Popen('taskkill /F /IM WhatsApp.exe', shell=True)
            return "Closed WhatsApp"
            
        elif any(w in app for w in ["zoom", "زوم"]):
            subprocess.Popen('taskkill /F /IM Zoom.exe', shell=True)
            return "Closed Zoom"

        elif any(w in app for w in ["spotify", "سبوتيفاي"]):
            subprocess.Popen('taskkill /F /IM Spotify.exe', shell=True)
            return "Closed Spotify"

        elif any(w in app for w in ["chrome", "browser", "متصفح", "كروم"]):
            subprocess.Popen('taskkill /F /IM chrome.exe', shell=True)
            return "Closed Web Browser"
            
        elif any(w in app for w in ["paint", "رسام"]):
            subprocess.Popen('taskkill /F /IM mspaint.exe', shell=True)
            return "Closed Paint"

        elif any(w in app for w in ["antigravity", "انتي جرافيتي", "انتيجرافيتي"]):
            subprocess.Popen('taskkill /F /IM "Antigravity IDE.exe"', shell=True)
            return "Closed Antigravity IDE"

        elif any(w in app for w in ["vscode", "vs code", "code", "في اس كود"]):
            subprocess.Popen('taskkill /F /IM Code.exe', shell=True)
            return "Closed VS Code"

        elif any(w in app for w in ["window", "نافذة", "شاشة", "اقفلي النافذة"]):
            pyautogui.hotkey('alt', 'f4')
            return "Closed active window"
            
        else:
            proc_name = app.replace(" ", "")
            subprocess.Popen(f'taskkill /F /IM {proc_name}.exe', shell=True)
            pyautogui.hotkey('alt', 'f4')
            return f"Closed {app_name}"
    except Exception as e:
        pyautogui.hotkey('alt', 'f4')
        return f"Attempted to close {app_name}: {str(e)}"
