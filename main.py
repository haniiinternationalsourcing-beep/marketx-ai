#!/usr/bin/env python3
"""MarketX AI - a live AI marketing-agent chat app for Android.

The app talks to Google Gemini (free API) over the internet. It does NOT
use canned answers: every reply is generated live by Gemini using the
agent system prompt below.

The friend pastes his OWN free Gemini API key (from aistudio.google.com)
on the Key screen. The key is stored only on the device, never logged,
never printed, never sent anywhere except to Google's Gemini API endpoint
as part of the request URL, which is how the Gemini API authenticates.
"""

import os
import threading

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

AGENT_NAME = "MarketX AI"

SYSTEM_PROMPT = (
    "You are MarketX AI, a professional marketing agent. Your job: "
    "(1) give marketing ideas for any business the user names, "
    "(2) tell current Instagram trends, "
    "(3) tell the best times to post Reels, "
    "(4) do simple market analysis when asked. "
    "Rules: professional business language, practical answers, no hype. "
    "Do NOT ask for any Instagram login or password, and do NOT offer "
    "to manage DMs or comments. Never promise followers, views, or "
    "earnings. First ask about the user's business: what they sell and "
    "who their customers are."
)

LANG_LINES = {
    "en": "Reply in English.",
    "hi": "Reply in Hindi written in Devanagari script.",
    "ur": "Reply in Roman Urdu (Urdu written in Latin script).",
}

LANG_NAMES = {"en": "English", "hi": "Hindi", "ur": "Roman Urdu"}

KEY_HELP = (
    "To chat live, add your free Gemini API key.\n\n"
    "How to get it (free, no credit card):\n"
    "1. Open aistudio.google.com in your browser.\n"
    "2. Sign in with your Google account.\n"
    "3. Tap 'Get API Key' and create a key.\n"
    "4. Paste the key here and tap Save.\n\n"
    "Your key stays only on this phone. It is never shared with anyone."
)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def key_path():
    return os.path.join(App.get_running_app().user_data_dir, "gemini_key.txt")


def load_key():
    try:
        with open(key_path(), "r") as f:
            return f.read().strip()
    except OSError:
        return ""


def save_key(value):
    path = key_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(value.strip())


def clear_key():
    try:
        os.remove(key_path())
    except OSError:
        pass


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lang = "en"
        self.waiting = False

        root = BoxLayout(orientation="vertical")

        # Header: app name + Key button
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=52)
        header.add_widget(Label(text=AGENT_NAME, bold=True, font_size=20))
        key_btn = Button(text="API Key", size_hint_x=None, width=100)
        key_btn.bind(on_release=self.go_key)
        header.add_widget(key_btn)
        root.add_widget(header)

        # Language picker
        lang_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=44)
        self.lang_btns = {}
        for code in ("en", "hi", "ur"):
            btn = Button(text=LANG_NAMES[code])
            btn.bind(on_release=lambda b, c=code: self.set_lang(c))
            self.lang_btns[code] = btn
            lang_row.add_widget(btn)
        root.add_widget(lang_row)
        self.refresh_lang_buttons()

        # Chat area
        self.chat_layout = GridLayout(cols=1, size_hint_y=None, spacing=6, padding=8)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.chat_layout)
        root.add_widget(scroll)

        # Input row
        input_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=52)
        self.input = TextInput(hint_text="Type your message...", multiline=False)
        self.input.bind(on_text_validate=lambda *a: self.send())
        send_btn = Button(text="Send", size_hint_x=None, width=90)
        send_btn.bind(on_release=lambda *a: self.send())
        input_row.add_widget(self.input)
        input_row.add_widget(send_btn)
        root.add_widget(input_row)

        self.add_widget(root)
        self.add_message(
            AGENT_NAME,
            "Hello! I am MarketX AI, your professional marketing agent.\n\n"
            "I can give you marketing ideas, Instagram trends, the best "
            "times to post Reels, and simple market analysis.\n\n"
            "To start, tell me about your business: what do you sell, "
            "and who are your customers?",
        )
        if not load_key():
            self.add_message(AGENT_NAME, KEY_HELP)

    def refresh_lang_buttons(self):
        for code, btn in self.lang_btns.items():
            if code == self.lang:
                btn.background_color = (0.2, 0.6, 1, 1)
            else:
                btn.background_color = (1, 1, 1, 1)

    def set_lang(self, code):
        self.lang = code
        self.refresh_lang_buttons()
        self.add_message(
            AGENT_NAME,
            "Language set to %s. I will now reply in %s."
            % (LANG_NAMES[code], LANG_NAMES[code]),
        )

    def go_key(self, *args):
        self.manager.current = "key"

    def add_message(self, sender, text):
        label = Label(
            text="%s:\n%s" % (sender, text),
            text_size=(None, None),
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        label.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w - 16, None))
        )
        label.bind(
            texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + 16)
        )
        self.chat_layout.add_widget(label)
        return label

    def send(self):
        text = self.input.text.strip()
        if not text or self.waiting:
            return
        self.input.text = ""
        self.add_message("You", text)
        key = load_key()
        if not key:
            self.add_message(AGENT_NAME, KEY_HELP)
            return
        self.waiting = True
        thinking = self.add_message(AGENT_NAME, "Thinking...")
        threading.Thread(
            target=self.call_gemini, args=(key, text, thinking), daemon=True
        ).start()

    def call_gemini(self, key, text, thinking_label):
        system = SYSTEM_PROMPT + " " + LANG_LINES[self.lang]
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": text}]}],
        }
        try:
            resp = requests.post(
                GEMINI_URL, params={"key": key}, json=payload, timeout=60
            )
            data = resp.json()
            if "error" in data:
                err = data["error"]
                reply = (
                    "Sorry, the request failed (error %s: %s). "
                    "Please check your API key, your internet connection, "
                    "and try again."
                    % (err.get("code", "?"), err.get("message", "unknown error"))
                )
            else:
                reply = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:  # network down, timeout, bad response
            reply = (
                "Sorry, I could not reach the AI service: %s. "
                "Please check your internet connection and try again."
                % type(exc).__name__
            )
        Clock.schedule_once(lambda dt: self.finish_reply(thinking_label, reply))

    def finish_reply(self, thinking_label, reply):
        thinking_label.text = "%s:\n%s" % (AGENT_NAME, reply)
        self.waiting = False


class KeyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=16, spacing=12)
        root.add_widget(
            Label(text="Gemini API Key", bold=True, font_size=20,
                  size_hint_y=None, height=44)
        )
        root.add_widget(Label(text=KEY_HELP, halign="left", valign="top"))
        self.status = Label(text="", size_hint_y=None, height=30)
        root.add_widget(self.status)
        self.key_input = TextInput(
            hint_text="Paste your Gemini API key here",
            password=True, multiline=False, size_hint_y=None, height=48,
        )
        root.add_widget(self.key_input)
        save_btn = Button(text="Save Key", size_hint_y=None, height=52)
        save_btn.bind(on_release=self.save)
        root.add_widget(save_btn)
        clear_btn = Button(text="Remove Saved Key", size_hint_y=None, height=52)
        clear_btn.bind(on_release=self.clear)
        root.add_widget(clear_btn)
        back_btn = Button(text="Back to Chat", size_hint_y=None, height=52)
        back_btn.bind(on_release=lambda *a: setattr(self.manager, "current", "chat"))
        root.add_widget(back_btn)
        self.add_widget(root)

    def on_pre_enter(self):
        self.key_input.text = ""
        self.status.text = (
            "A key is already saved on this phone." if load_key()
            else "No key saved yet."
        )

    def save(self, *args):
        value = self.key_input.text.strip()
        if not value:
            self.status.text = "Please paste a key first."
            return
        save_key(value)
        self.key_input.text = ""
        self.status.text = "Key saved on this phone. Back to chat to start."

    def clear(self, *args):
        clear_key()
        self.key_input.text = ""
        self.status.text = "Saved key removed."


class MarketXApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(KeyScreen(name="key"))
        return sm


if __name__ == "__main__":
    MarketXApp().run()
