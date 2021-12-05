rmdir /s /q build
rmdir /s /q dist
copy "assets\ui\app.ico" app.ico
pyinstaller --onefile --windowed --icon=app.ico --name=altium_db_gui src/main.py
del app.ico