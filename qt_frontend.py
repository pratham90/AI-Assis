import sys
import requests
import speech_recognition as sr
import json
import os
import tempfile
import wave
import pyaudio
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QStackedWidget, QMessageBox, QFrame, QSpacerItem, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

# Hosted backend (Render)
BACKEND_URL = "https://ai-assis-54jg.onrender.com"


class LoginWidget(QWidget):
    def __new__(cls, *args, **kwargs):
        if QApplication.instance() is None:
            raise RuntimeError("QApplication must be constructed before any QWidget (including LoginWidget). Run this script directly, not as an import.")
        return super().__new__(cls)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setStyleSheet("background: rgba(0,0,0,0.85);")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 60, 0, 0)

        # Card
        card = QFrame()
        card.setStyleSheet("background: rgba(0,0,0,0.7); border-radius: 18px; border: 1px solid #333;")
        card.setFixedSize(420, 360)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(18)

        title = QLabel("🔒 Login / Signup")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #fff;")
        card_layout.addWidget(title)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFont(QFont("Segoe UI", 13))
        self.email_input.setFixedHeight(44)
        self.email_input.setStyleSheet("border-radius: 8px; padding: 8px; background: rgba(255,255,255,0.15); border: none; color: #fff;")
        card_layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Segoe UI", 13))
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet("border-radius: 8px; padding: 8px; background: rgba(255,255,255,0.15); border: none; color: #fff;")
        card_layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.login_btn.setFixedHeight(44)
        self.login_btn.setStyleSheet("border-radius: 8px; background: #3388FF; color: white; padding: 10px 0; border: none;")
        self.login_btn.clicked.connect(self.login)
        card_layout.addWidget(self.login_btn)

        self.signup_btn = QPushButton("New user? Sign up")
        self.signup_btn.setFont(QFont("Segoe UI", 12))
        self.signup_btn.setFixedHeight(38)
        self.signup_btn.setStyleSheet("border-radius: 8px; background: transparent; color: #4F8CFF; border: none;")
        self.signup_btn.clicked.connect(self.signup)
        card_layout.addWidget(self.signup_btn)

        self.status_label = QLabel("")
        font = QFont("Segoe UI", 10)
        font.setItalic(True)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #fff;")

        from PySide6.QtWidgets import QCheckBox
        self.remember_me = QCheckBox("Remember me for 7 days")
        self.remember_me.setStyleSheet("color: #fff;")
        card_layout.insertWidget(3, self.remember_me)

        # Auto-login if session exists
        self.try_auto_login()
        card_layout.addWidget(self.status_label)
        layout.addWidget(card, alignment=Qt.AlignCenter)

    def try_auto_login(self):
        session_file = os.path.expanduser("~/.ai_assistant_session.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                import time
                if time.time() - data.get("timestamp", 0) < 7*24*3600:
                    self.parent.email = data["email"]
                    self.parent.password = data["password"]
                    self.parent.get_credits()
                    self.parent.show_main()
                    return True
            except Exception:
                pass
        return False

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both email and password.")
            return
        self.status_label.setText("Logging in...")
        QApplication.processEvents()
        try:
            res = requests.post(f"{BACKEND_URL}/login", json={"email": email, "password": password}, timeout=12)
            data = res.json()
            if data.get("success"):
                self.parent.email = email
                self.parent.password = password
                self.parent.get_credits()
                self.parent.show_main()
                # Save session if remember me is checked
                if self.remember_me.isChecked():
                    session_file = os.path.expanduser("~/.ai_assistant_session.json")
                    with open(session_file, "w") as f:
                        json.dump({"email": email, "password": password, "timestamp": __import__('time').time()}, f)
            else:
                QMessageBox.warning(self, "Login Failed", data.get("message", "Login failed"))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        self.status_label.setText("")

    def signup(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or not password:
            QMessageBox.warning(self, "Signup Failed", "Please enter both email and password.")
            return
        self.status_label.setText("Signing up...")
        QApplication.processEvents()
        try:
            res = requests.post(f"{BACKEND_URL}/signup", json={"email": email, "password": password}, timeout=12)
            data = res.json()
            if data.get("success"):
                QMessageBox.information(self, "Signup Success", "Account created! Please log in.")
            else:
                QMessageBox.warning(self, "Signup Failed", data.get("message", "Signup failed"))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        self.status_label.setText("")


class MainWidget(QWidget):
    def __new__(cls, *args, **kwargs):
        if QApplication.instance() is None:
            raise RuntimeError("QApplication must be constructed before any QWidget (including MainWidget). Run this script directly, not as an import.")
        return super().__new__(cls)

    def setup_hotkeys(self):
        from PySide6.QtGui import QShortcut, QKeySequence
        self.shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_quit.activated.connect(self.quit_app)
        self.shortcut_upload = QShortcut(QKeySequence("Ctrl+U"), self)
        self.shortcut_upload.activated.connect(self.upload_resume)
        self.shortcut_smart = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_smart.activated.connect(self.toggle_smart_mode)
        self.shortcut_hide = QShortcut(QKeySequence("Ctrl+H"), self)
        self.shortcut_hide.activated.connect(self.toggle_hide)

    def quit_app(self):
        QApplication.quit()

    def toggle_hide(self):
        if self.isVisible():
            self.hide()
            from PySide6.QtGui import QKeySequence, QShortcut
            self._unhide_shortcut = QShortcut(QKeySequence("Ctrl+H"), self.parent)
            self._unhide_shortcut.activated.connect(self.show_again)
        else:
            self.show_again()

    def show_again(self):
        self.show()
        if hasattr(self, '_unhide_shortcut'):
            self._unhide_shortcut.setEnabled(False)
            del self._unhide_shortcut

    def toggle_smart_mode(self):
        self._smart_mode = not getattr(self, '_smart_mode', False)
        self.smart_mode.setText(f"Smart mode: {'ON' if self._smart_mode else 'OFF'}")
        if self._smart_mode and not getattr(self, 'resume_path', None):
            QMessageBox.information(self, "Smart Mode", "Smart mode is ON. Upload a resume (Ctrl+U) to use resume context.")

    def upload_resume(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Select Resume (PDF or TXT)", os.path.expanduser("~"), "Documents (*.pdf *.txt);;All Files (*)")
        if path:
            self.resume_path = path
            self.answers_box.append(f"[DEBUG] Loaded resume: {os.path.basename(path)}")
            if not getattr(self, '_smart_mode', False):
                self.toggle_smart_mode()

    def start_listening(self):
        if getattr(self, 'listening', False):
            return
        self.status_label.setText("Listening... (Speak now)")
        self.mic_button.setText("🛑 Stop Listening")
        try:
            self.mic_button.clicked.disconnect()
        except Exception:
            pass
        self.mic_button.clicked.connect(self.stop_listening)
        self.listening = True
        self.recognizer = sr.Recognizer()
        # Robust mic selection
        try:
            mic_index = None
            mic_name = None
            if hasattr(self, 'mic_selector') and self.mic_selector.count() > 0:
                # stored device index in item data
                mic_index = self.mic_selector.currentData()
                mic_name = self.mic_selector.currentText()
            else:
                mic_list = sr.Microphone.list_microphone_names()
                pa = pyaudio.PyAudio()
                for i in range(pa.get_device_count()):
                    info = pa.get_device_info_by_index(i)
                    if info.get('maxInputChannels', 0) > 0:
                        mic_index = i
                        mic_name = info.get('name', mic_list[i] if i < len(mic_list) else f'Device {i}')
                        break
                pa.terminate()
                if mic_index is None and mic_list:
                    mic_index = 0
                    mic_name = mic_list[0]
            if mic_index is not None:
                self.status_label.setText(f"Using mic: {mic_name}. Listening... (Speak now)")
                self.selected_mic_index = mic_index
            else:
                raise Exception("No microphone found. Please connect a mic or headset.")
        except Exception as e:
            self.status_label.setText(f"Microphone error: {e}")
            self.answers_box.append(f"[DEBUG] Microphone error: {e}")
            self.listening = False
            return
        self.listen_real()

    def stop_listening(self):
        self.status_label.setText("")
        self.mic_button.setText("🎤 Start Listening")
        try:
            self.mic_button.clicked.disconnect()
        except Exception:
            pass
        self.mic_button.clicked.connect(self.start_listening)
        self.listening = False

    def _local_stt_fallback(self, frames, sample_rate, sample_width):
        try:
            audio_data = sr.AudioData(b"".join(frames), sample_rate, sample_width)
            text = self.recognizer.recognize_google(audio_data)
            return text
        except Exception as e:
            self.answers_box.append(f"[DEBUG] Local STT fallback failed: {e}")
            return ""

    def listen_real(self):
        if not self.listening:
            return
        try:
            self.answers_box.append("[DEBUG] Recording audio with PyAudio...")
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            RECORD_SECONDS = 5
            p = pyaudio.PyAudio()
            mic_index = getattr(self, 'selected_mic_index', None)
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=mic_index)
            frames = []
            self.status_label.setText("Listening... (Speak now)")
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                if not self.listening:
                    break
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            sampwidth = p.get_sample_size(FORMAT)
            p.terminate()

            # Optional calibration to improve SNR
            try:
                with sr.Microphone(device_index=mic_index) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
            except Exception:
                pass

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
                tmp_wav_path = tmp_wav.name
            with wave.open(tmp_wav_path, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(sampwidth)
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))

            self.answers_box.append(f"[DEBUG] Sending audio to backend for recognition...")
            recognized_text = ""
            try:
                with open(tmp_wav_path, 'rb') as f:
                    files = {'audio': ('audio.wav', f, 'audio/wav')}
                    res = requests.post(f"{BACKEND_URL}/listen", files=files, timeout=60)
                if res.status_code == 200:
                    data = res.json()
                    recognized_text = (data.get('text') or data.get('transcript') or '').strip()
                    if not recognized_text and isinstance(data, dict):
                        recognized_text = (data.get('data', {}) or {}).get('text', '')
                else:
                    self.answers_box.append(f"[DEBUG] Backend /listen error: {res.status_code} {res.text}")
            except Exception as e:
                self.answers_box.append(f"[DEBUG] Error contacting backend /listen: {e}")

            if not recognized_text:
                self.answers_box.append("[DEBUG] Falling back to local STT (Google)...")
                recognized_text = self._local_stt_fallback(frames, RATE, sampwidth)
                if not recognized_text:
                    try:
                        import pocketsphinx  # noqa: F401
                        self.answers_box.append("[DEBUG] Trying offline STT (Sphinx)...")
                        audio_data = sr.AudioData(b"".join(frames), RATE, sampwidth)
                        recognized_text = self.recognizer.recognize_sphinx(audio_data)
                    except Exception as e:
                        self.answers_box.append(f"[DEBUG] Offline STT unavailable or failed: {e}")

            if recognized_text:
                self.answers_box.append(f"[DEBUG] Recognized: {recognized_text}")
                self.status_label.setText(f"Heard: {recognized_text}")
                self.display_question_and_answer(recognized_text)
            else:
                self.status_label.setText("Could not understand audio.")
                self.answers_box.append("[DEBUG] No speech recognized.")

            try:
                os.remove(tmp_wav_path)
            except Exception:
                pass
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            self.answers_box.append(f"[DEBUG] Error: {e}")
        if self.listening:
            QTimer.singleShot(100, self.listen_real)

    def display_question_and_answer(self, question):
        self.answers_box.append(f"Q: {question}")
        self.status_label.setText("Getting answer...")
        QApplication.processEvents()
        try:
            answer = None
            # Smart mode with resume upload: try resume first, then fallback to global
            if getattr(self, '_smart_mode', False) and getattr(self, 'resume_path', None):
                try:
                    with open(self.resume_path, 'rb') as f:
                        files = {'resume': (os.path.basename(self.resume_path), f, 'application/pdf' if self.resume_path.lower().endswith('.pdf') else 'text/plain')}
                        data = {
                            'email': self.parent.email,
                            'question': question,
                            'mode': 'resume'
                        }
                        res = requests.post(f"{BACKEND_URL}/ask", files=files, data=data, timeout=90)
                    if res.status_code == 200:
                        rdata = res.json()
                        answer = (rdata.get("answer") or "").strip()
                        if not answer:
                            self.answers_box.append("[DEBUG] Empty answer in resume mode. Falling back to global.")
                    else:
                        # 4xx/5xx: fallback to global
                        self.answers_box.append(f"[DEBUG] Resume mode failed: {res.status_code}. Falling back to global.")
                except Exception as e:
                    self.answers_box.append(f"[DEBUG] Error in resume mode: {e}. Falling back to global.")

            if not answer:
                # Global/general mode
                try:
                    res = requests.post(f"{BACKEND_URL}/ask", json={"email": self.parent.email, "question": question, "mode": "global"}, timeout=60)
                    if res.status_code == 403:
                        # No credits left
                        try:
                            msg = res.json().get('answer', 'No credits left.')
                        except Exception:
                            msg = 'No credits left.'
                        self.answers_box.append(f"A: {msg}\n")
                        self.status_label.setText("")
                        return
                    rdata = res.json()
                    answer = (rdata.get("answer") or "No answer.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                    answer = "No answer."

            self.answers_box.append(f"A: {answer}\n")
            self.parent.get_credits()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        self.status_label.setText("")

    def ask(self):
        pass  # Disable manual ask

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._smart_mode = False
        self.resume_path = None
        self.setStyleSheet("background: rgba(0,0,0,0.85);")
        self.init_ui()
        self.setup_hotkeys()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setStyleSheet("background: rgba(0,0,0,0.95); border-bottom: 0px solid #222; border-radius: 0;")
        topbar.setFixedHeight(48)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(18, 0, 18, 0)
        topbar_layout.setSpacing(16)
        bulb = QLabel("💡")
        bulb.setFont(QFont("Segoe UI", 18))
        topbar_layout.addWidget(bulb)
        title = QLabel("Live insights")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #fff;")
        topbar_layout.addWidget(title)
        self.smart_mode = QLabel("Smart mode: OFF")
        self.smart_mode.setFont(QFont("Segoe UI", 13))
        self.smart_mode.setStyleSheet("color: #fff;")
        topbar_layout.addWidget(self.smart_mode)
        self.credits_label = QLabel("Credits: 0")
        self.credits_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.credits_label.setStyleSheet("color: #4EE44E;")
        topbar_layout.addWidget(self.credits_label)
        topbar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        logout_btn = QPushButton("Logout")
        logout_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        logout_btn.setStyleSheet("background: transparent; color: #fff; border: none;")
        logout_btn.clicked.connect(self.parent.show_login)
        topbar_layout.addWidget(logout_btn)
        layout.addWidget(topbar)

        # Hotkeys label
        hotkey_label = QLabel("<b>Hotkeys:</b>  <span style='color:#fff'>Ctrl+Q</span> = Quit  |  <span style='color:#fff'>Ctrl+U</span> = Upload Resume  |  <span style='color:#fff'>Ctrl+S</span> = Smart Mode  |  <span style='color:#fff'>Ctrl+H</span> = Hide/Unhide")
        hotkey_label.setStyleSheet("color: #4F8CFF; font-size: 16px; background: rgba(0,0,0,0.95); padding: 8px 0; border: none; margin: 0; border-radius: 0;")
        hotkey_label.setMinimumWidth(900)
        layout.addWidget(hotkey_label, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # Main card
        card = QFrame()
        card.setStyleSheet("background: rgba(0,0,0,0.7); border-radius: 0 0 18px 18px; border: 1px solid #333; border-top: none;")
        card.setFixedSize(900, 370)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Left column
        left = QFrame()
        left.setStyleSheet("background: transparent; border-top-left-radius: 18px; border-bottom-left-radius: 18px;")
        left.setFixedWidth(320)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(16)
        q_label = QLabel("Questions")
        q_label.setStyleSheet("color: #fff;")
        left_layout.addWidget(q_label)

        # Microphone selection row
        from PySide6.QtWidgets import QComboBox
        mic_row = QHBoxLayout()
        self.mic_selector = QComboBox()
        self.mic_selector.setStyleSheet("background: rgba(255,255,255,0.1); color: #fff; border-radius: 6px; padding: 4px;")
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedWidth(34)
        refresh_btn.setStyleSheet("background: #111; color: #aaa; border-radius: 6px;")
        refresh_btn.clicked.connect(self._load_mics)
        calib_btn = QPushButton("Calibrate")
        calib_btn.setStyleSheet("background: #111; color: #4F8CFF; border-radius: 6px; padding: 4px 8px;")
        calib_btn.clicked.connect(self._calibrate)
        mic_row.addWidget(self.mic_selector)
        mic_row.addWidget(refresh_btn)
        mic_row.addWidget(calib_btn)
        left_layout.addLayout(mic_row)

        self.mic_button = QPushButton("🎤 Start Listening", self)
        self.mic_button.setCursor(Qt.PointingHandCursor)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: #111;
                color: #4F8CFF;
                border-radius: 18px;
                padding: 10px 30px;
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #222;
            }
        """)
        self.mic_button.clicked.connect(self.start_listening)
        left_layout.addWidget(self.mic_button)
        self.status_label = QLabel("")
        font = QFont("Segoe UI", 10)
        font.setItalic(True)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #fff;")
        left_layout.addWidget(self.status_label)
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        card_layout.addWidget(left)

        # Right column
        right = QFrame()
        right.setStyleSheet("background: transparent; border-top-right-radius: 18px; border-bottom-right-radius: 18px;")
        right.setFixedWidth(320)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)
        a_label = QLabel("Answers")
        a_label.setStyleSheet("color: #fff;")
        right_layout.addWidget(a_label)
        self.answers_box = QTextEdit()
        self.answers_box.setFont(QFont("Segoe UI", 12))
        self.answers_box.setStyleSheet("border-radius: 8px; background: rgba(255,255,255,0.10); border: none; color: #fff; outline: none;")
        self.answers_box.setReadOnly(True)
        right_layout.addWidget(self.answers_box)
        card_layout.addWidget(right)

        layout.addWidget(card, alignment=Qt.AlignCenter)
        
        # Initialize mic list on first load
        QTimer.singleShot(0, self._load_mics)

    def _load_mics(self):
        try:
            self.mic_selector.clear()
            pa = pyaudio.PyAudio()
            count = pa.get_device_count()
            added = 0
            for i in range(count):
                info = pa.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    name = info.get('name', f'Device {i}')
                    self.mic_selector.addItem(name, i)
                    added += 1
            pa.terminate()
            if added == 0:
                self.mic_selector.addItem("No input devices found", None)
            self.answers_box.append(f"[DEBUG] Mic devices loaded: {added}")
        except Exception as e:
            self.answers_box.append(f"[DEBUG] Failed to load mic devices: {e}")

    def _calibrate(self):
        try:
            idx = self.mic_selector.currentData()
            if idx is None:
                QMessageBox.warning(self, "Calibration", "No input device selected.")
                return
            with sr.Microphone(device_index=idx) as source:
                self.answers_box.append("[DEBUG] Calibrating... please stay quiet")
                self.recognizer = getattr(self, 'recognizer', sr.Recognizer())
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                self.answers_box.append("[DEBUG] Calibration complete")
        except Exception as e:
            self.answers_box.append(f"[DEBUG] Calibration failed: {e}")

    def ask(self):
        pass  # Disable manual ask


class MainWindow(QWidget):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live insights - Modern Qt UI")
        self.setWindowIcon(QIcon())
        self.setMinimumSize(700, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.93)
        self.email = ""
        self.password = ""
        self.credits = 0
        self.stack = QStackedWidget(self)
        self.login_widget = LoginWidget(self)
        self.main_widget = MainWidget(self)
        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.main_widget)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        self.show_login()

    def show_login(self):
        self.stack.setCurrentWidget(self.login_widget)
        # Clear any persisted session on logout
        try:
            session_file = os.path.expanduser("~/.ai_assistant_session.json")
            if os.path.exists(session_file):
                os.remove(session_file)
        except Exception:
            pass

    def show_main(self):
        self.main_widget.credits_label.setText(f"Credits: {self.credits}")
        self.stack.setCurrentWidget(self.main_widget)

    def get_credits(self):
        try:
            res = requests.post(f"{BACKEND_URL}/get_credits", json={"email": self.email, "password": self.password}, timeout=12)
            data = res.json()
            if data.get("success"):
                self.credits = data.get("credits", 0)
                self.main_widget.credits_label.setText(f"Credits: {self.credits}")
        except Exception:
            self.credits = 0
            self.main_widget.credits_label.setText(f"Credits: {self.credits}")


if __name__ == "__main__":
    print("[DEBUG] Creating QApplication...")
    app = QApplication(sys.argv)
    print("[DEBUG] QApplication created. Now creating MainWindow...")
    window = MainWindow()
    window.show()
    print("[DEBUG] MainWindow shown. Entering app.exec()...")
    sys.exit(app.exec())