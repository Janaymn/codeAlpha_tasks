import os
import json
from dotenv import load_dotenv
import laptop_tools

# Load environment variables from .env file (override system env)
load_dotenv(override=True)

SYSTEM_PROMPT = """You are an intelligent, warm, witty, and highly capable Egyptian female AI assistant with full access and control over the user's laptop.

Persona Traits:
- Tone: Warm, energetic, polite, clever, and distinctly Egyptian ("مساعدة مصرية ذكية وبشوشة وجدعة").
- Language: Speak in natural, friendly Egyptian Arabic (اللهجة المصرية العامة) or clear English depending on how the user speaks to you. Use common Egyptian polite expressions naturally such as: "من عيوني!", "أمرك يا فندم", "تحت أمرك", "من عينيا الجوز", "تمام جداً", "ثانية واحدة هظبطهالك".

Intent Understanding & Tool Usage (NO KEYWORDS REQUIRED):
- Do NOT look for exact fixed keywords or specific phrases. Intelligently deduce the user's underlying intent from their natural conversational speech in Arabic or English!
- If the user expresses a desire to write something, take notes, compose a document, write a list, or dictate text -> Invoke `dictate_to_notepad` or `dictate_to_word`.
- If the user mentions calculating numbers, doing math, or solving equations -> Invoke `open_application` with `app_name="calculator"`.
- If the user mentions watching a movie, video, listening to music, or searching for a clip -> Invoke `play_on_youtube` or `open_netflix_movie`.
- If the user mentions opening any software, web browser, file folder, terminal, or app on their computer -> Invoke `open_application` with the app name.
- If the user says an application did not open, asks to re-open it, or wants a fresh window -> Invoke `open_application` with `force=True`.
- If the user asks to close, exit, or terminate an application or active window (e.g. 'اقفلي الورد', 'اقفلي النوت باد', 'close Chrome', 'اقفلي النافذة') -> Invoke `close_application` with the app name.
- If the user wants current information, news, or answers to complex real-world queries -> Invoke `search_google`.
- If the user asks about time, date, or timezone -> Invoke `get_system_time`.

Response Style:
- Keep spoken responses concise, conversational, and natural for voice output.
- After a tool executes, explain what you did naturally in your warm Egyptian female persona.
"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Opens or re-opens an application on the laptop (Notepad, Word, Calculator, Chrome, WhatsApp, Zoom, Explorer, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to open (e.g. 'notepad', 'word', 'whatsapp', 'zoom', 'calculator', 'chrome')"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Set to true if the user states the application did not open, asks to re-open it, or wants a new window."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Closes or terminates an application on the laptop (Notepad, Word, Calculator, Chrome, WhatsApp, Zoom, etc.) or active window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to close (e.g. 'notepad', 'word', 'whatsapp', 'chrome', 'zoom', 'calculator', 'active_window')"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dictate_to_notepad",
            "description": "Opens Notepad and starts live voice dictation mode to write text into Notepad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_to_write": {
                        "type": "string",
                        "description": "Optional initial text to write into Notepad immediately"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dictate_to_word",
            "description": "Opens Microsoft Word and starts live voice dictation mode to write text into Word.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_to_write": {
                        "type": "string",
                        "description": "Optional initial text to write into Microsoft Word immediately"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_on_youtube",
            "description": "Plays a song or video query on YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "song_name": {
                        "type": "string",
                        "description": "Title or query of the video/song to play on YouTube"
                    }
                },
                "required": ["song_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_netflix_movie",
            "description": "Searches for and opens a movie or show on Netflix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_name": {
                        "type": "string",
                        "description": "The title of the movie or show to search on Netflix"
                    }
                },
                "required": ["movie_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_time",
            "description": "Gets current time formatted for a specific timezone or country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone_str": {
                        "type": "string",
                        "description": "Timezone or city name (e.g. 'Africa/Cairo', 'UTC', 'Tokyo')"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Searches the web via Google for current info, news, or general search queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The web search query string"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

class GroqAIEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        if "llama" in model_name.lower():
            model_name = "openai/gpt-oss-120b"
        self.model = model_name
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            print("\n[WARNING] GROQ_API_KEY is missing or set to placeholder in .env!\n")
            return

        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key, timeout=12.0)
        except Exception as e:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1",
                    timeout=12.0
                )
            except Exception as ex:
                print(f"[Error] Could not initialize Groq client: {ex}")

    def execute_tool(self, tool_name: str, args: dict, listen_func, talk_func) -> str:
        """Executes the requested laptop tool and returns the status string."""
        if tool_name == "open_application":
            return laptop_tools.open_application(args.get("app_name", ""), force=args.get("force", False))
        elif tool_name == "close_application":
            return laptop_tools.close_application(args.get("app_name", ""))
        elif tool_name == "dictate_to_notepad":
            init_txt = args.get("text_to_write") or args.get("initial_text", "")
            return laptop_tools.dictate_to_notepad(listen_func, talk_func, initial_text=init_txt)
        elif tool_name == "dictate_to_word":
            init_txt = args.get("text_to_write") or args.get("initial_text", "")
            return laptop_tools.dictate_to_word(listen_func, talk_func, initial_text=init_txt)
        elif tool_name == "play_on_youtube":
            return laptop_tools.play_on_youtube(args.get("song_name", ""))
        elif tool_name == "open_netflix_movie":
            return laptop_tools.open_netflix_movie(args.get("movie_name", ""))
        elif tool_name == "get_system_time":
            return laptop_tools.get_system_time(args.get("timezone_str", "Africa/Cairo"))
        elif tool_name == "search_google":
            return laptop_tools.search_google(args.get("query", ""))
        return f"Tool {tool_name} completed."

    def chat(self, user_input: str, listen_func=None, talk_func=None) -> str:
        """
        Sends user speech input to Groq LLM.
        If tools are called, executes them, feeds the result back to the model,
        and returns the model's self-generated natural response string.
        """
        if not user_input or user_input.strip() == "":
            return ""

        if not self.client:
            self._init_client()
            if not self.client:
                return "مفتاح Groq API مش موجود في ملف الـ .env."

        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            # First turn: model decides whether to call tools or reply directly
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.6,
                max_tokens=300
            )

            response_message = response.choices[0].message
            tool_calls = getattr(response_message, "tool_calls", None)

            if tool_calls and len(tool_calls) > 0:
                # Add assistant tool call intent to conversation history
                self.conversation_history.append(response_message)

                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                    print(f" [Tool Execution]: {func_name} -> {func_args}")
                    tool_result = self.execute_tool(func_name, func_args, listen_func, talk_func)

                    # Append tool execution result back to conversation history
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    })

                # Second turn: LLM model generates its OWN natural response summarizing the action
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=TOOLS_SCHEMA,
                    temperature=0.6,
                    max_tokens=50
                )
                final_reply = second_response.choices[0].message.content or "تمام اتنفذت الفكرة!"
                self.conversation_history.append({"role": "assistant", "content": final_reply})
                return final_reply

            else:
                reply_text = response_message.content or "تحت أمرك يا جميل!"
                self.conversation_history.append({"role": "assistant", "content": reply_text})
                return reply_text

        except Exception as e:
            print(f"[Groq Chat Error]: {e}")
            return "حصلت معلش لغبطة بسيطة في الاتصال، ممكن تعيدي كلامك تاني يا جميل؟"
