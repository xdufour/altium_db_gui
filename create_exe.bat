rmdir /s /q build
rmdir /s /q dist
pyinstaller --onefile --icon=app.ico src/main.py