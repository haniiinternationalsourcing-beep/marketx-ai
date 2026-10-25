# MarketX AI

A live AI marketing-agent chat app for Android.

- Chat UI with a language picker: English, Hindi (Devanagari), Roman Urdu.
- Replies are generated live by Google Gemini (free API) — no canned answers.
- The user pastes their OWN free Gemini API key (from aistudio.google.com)
  on the API Key screen. The key is stored only on the device (localStorage).
- No API key is stored in this repo. No Instagram account management.

## Build history

- Attempt 1 and 2 used Kivy + python-for-android via the kivy/buildozer
  Docker image. Both failed: the current python-for-android builds
  CPython 3.14, for which no pyjnius/kivy wheels exist and whose C API
  breaks kivy 2.3.0's generated C code — even with the Docker image pinned
  to the exact digest that built Panther AI on 2026-10-15.
- Attempt 3 (current): a native Android WebView app under `android/`,
  built by GitHub Actions with Gradle. Same app behavior, no Python
  toolchain involved.
