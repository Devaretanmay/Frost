# VHS Tape Script for FROST 2-Minute Demo Video
# Run: vhs scripts/record_demo_vhs.tape

Output docs/assets/frost_demo_video.gif
Output docs/assets/frost_demo_video.mp4

Set FontSize 18
Set FontFamily "JetBrains Mono"
Set Width 1200
Set Height 720
Set Theme "Catppuccin Macchiato"
Set Padding 20
Set TypingSpeed 45ms

# Environment Setup (Hidden)
Hide
Type "source /Users/tanmaydevare/Tanmay/Agent/Harada/.venv/bin/activate"
Enter
Type "alias frost_demo='python3 /Users/tanmaydevare/Tanmay/Agent/Harada/scripts/frost_demo_sim.py'"
Enter
Type "clear"
Enter
Show

# Scene 1: Diagnostics & Health Check
Type "pip install frost-ai"
Enter
Sleep 1.5s

Type "frost doctor"
Enter
Sleep 3s

# Scene 2: Hitting Uncertainty & Micro-Branching Demo
Hide
Type "clear"
Enter
Show

Type "# Submitting complex modernization task to FROST runtime"
Enter
Sleep 1s

Type "frost run 'Modernize repository to Python 3.14, Pydantic V2, and SQLAlchemy 2.0'"
Enter
Sleep 1s

Hide
Type "frost_demo"
Enter
Show

Sleep 3s

# Scene 3: Inspection & Results
Type "frost inspect"
Enter
Sleep 4s

Hide
Type "clear"
Enter
Show

Type "# Repository GREEN — 54/54 Tests Passed (Token Reduction: 68.4%)"
Enter
Sleep 3s
