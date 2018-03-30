# build a Mac application bundle for Feldman using pyinstaller
pyinstaller --clean --onefile --name "Feldman" --windowed --icon assets/feldmanicon.icns qtmain.py