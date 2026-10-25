[app]

# (str) Title of your application
title = MarketX AI

# (str) Package name
package.name = marketxai

# (str) Package domain (needed for android/ios packaging)
package.domain = com.marketxai

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json,txt

# (str) Application version
version = 1.0

# (list) Application requirements
# `openssl` is REQUIRED: without this p4a recipe, Python's ssl module is
# missing on Android and every HTTPS call crashes with SSLError.
requirements = python3,kivy==2.3.0,openssl,requests

# (str) Supported orientations
orientation = portrait

# (list) Android permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 34

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android architectures (single arm64-v8a covers all modern devices)
android.archs = arm64-v8a

# (bool) Automatically accept Android SDK licenses (non-interactive CI)
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (str) python-for-android branch
p4a.branch = master

# (bool) Suppress the interactive "running as root?" prompt in CI
warn_on_root = 0
