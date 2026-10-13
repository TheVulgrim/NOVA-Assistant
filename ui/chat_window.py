import sys
import platform
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QEvent
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLineEdit,
    QPushButton,
    QLabel,
    QFrame,
    QApplication,
    QGraphicsDropShadowEffect,
)

import core.router
import core.intent
import skills.system_skills
from core.speech_output import speak
from ui.viewport_3d import Model3DViewport

try:
    import core.speech_input
    SPEECH_INPUT_AVAILABLE = True
except ImportError:
    SPEECH_INPUT_AVAILABLE = False


class IntentWorker(QThread):
    """Worker thread to run intent classification and TTS without blocking the GUI."""
    response_ready = pyqtSignal(str)
    speech_finished = pyqtSignal()

    def __init__(self, command: str, speak_output: bool = True):
        super().__init__()
        self.command = command
        self.speak_output = speak_output

    def run(self):
        try:
            response = core.intent.runtime(self.command)
        except (ConnectionError, TimeoutError, ValueError, OSError, Exception):
            response = core.router.route(self.command)

        response_str = str(response)
        self.response_ready.emit(response_str)

        if self.speak_output:
            speak(response_str)

        self.speech_finished.emit()


class VoiceInputWorker(QThread):
    """Worker thread for speech-to-text to keep GUI responsive while listening."""
    recognized_text = pyqtSignal(str)
    listening_finished = pyqtSignal()

    def run(self):
        if SPEECH_INPUT_AVAILABLE:
            try:
                text = core.speech_input.listen()
                if text:
                    self.recognized_text.emit(text)
            except Exception:
                pass
        self.listening_finished.emit()


class CompactChatBubble(QFrame):
    """Compact chat bubble widget with sleek dark glass styling."""

    def __init__(self, sender: str, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)

        # Sender tag
        sender_lbl = QLabel(sender)
        sender_lbl.setStyleSheet(
            "font-size: 10px; font-weight: bold; "
            + ("color: #00d2ff;" if is_user else "color: #7e95b0;")
        )
        layout.addWidget(sender_lbl)

        # Message body
        body_lbl = QLabel(text)
        body_lbl.setWordWrap(True)
        body_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        if "+---" in text or "|" in text:
            body_lbl.setFont(QFont("Monospace", 8))
        else:
            body_lbl.setFont(QFont("Arial", 9))

        if is_user:
            self.setStyleSheet(
                "QFrame { background-color: rgba(23, 53, 82, 0.85); border-radius: 10px; border: 1px solid rgba(0, 210, 255, 0.25); }"
                "QLabel { color: #f0f6fc; }"
            )
        else:
            self.setStyleSheet(
                "QFrame { background-color: rgba(28, 33, 46, 0.85); border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.08); }"
                "QLabel { color: #dce3ed; }"
            )

        layout.addWidget(body_lbl)


# Backwards compatibility alias
ChatBubble = CompactChatBubble


class NovaFloatingAvatar(QWidget):
    """
    Borderless, transparent, floating desktop avatar/pet widget for NOVA.
    
    Features:
    - Frameless, translucent background, stays on top of all windows.
    - Freely draggable anywhere across the screen.
    - Click avatar to toggle compact glassmorphism chat popover panel.
    - Fully asynchronous worker threads for non-blocking intent & Google TTS.
    - Dynamic mood animations in the 3D model viewport (idle, listening, thinking, speaking).
    """

    AVATAR_SIZE = 190
    POPOVER_WIDTH = 340
    POPOVER_HEIGHT = 330

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVA — Desktop Assistant")

        # 1. Desktop Floating Avatar Window Setup
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NativeWindow, True)

        # Interaction state
        self._press_global_pos = None
        self._press_local_pos = None
        self._drag_start_offset = None
        self._is_dragging = False
        self._system_move_active = False
        self._popover_open = False

        self.current_worker = None
        self.voice_worker = None

        self._build_ui()
        self._apply_styles()

        # Start collapsed to just the floating avatar
        self._update_geometry(popover_visible=False)

        # Initial subtle greeting in background thread
        self._post_assistant_message("System's Online. Click me to chat, Boss!", speak_now=True)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #e1e7f0;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(14, 18, 26, 0.4);
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 210, 255, 0.3);
                min-height: 16px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00d2ff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)
        self.main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # ------------------- 1. AVATAR CONTAINER (DRAGGABLE & CLICKABLE) -------------------
        self.avatar_container = QFrame(self)
        self.avatar_container.setFixedSize(self.AVATAR_SIZE, self.AVATAR_SIZE)
        self.avatar_container.setCursor(QCursor(Qt.OpenHandCursor))
        self.avatar_container.setStyleSheet("background: transparent; border: none;")

        avatar_layout = QVBoxLayout(self.avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setSpacing(2)

        # 3D Viewport core
        self.viewport_3d = Model3DViewport(self.avatar_container, transparent_bg=True, compact=True)
        avatar_layout.addWidget(self.viewport_3d, 1)

        # Sleek mini status pill below core
        self.status_pill = QLabel("• IDLE", self.avatar_container)
        self.status_pill.setAlignment(Qt.AlignCenter)
        self.status_pill.setStyleSheet("""
            QLabel {
                background-color: rgba(14, 18, 28, 0.85);
                color: #00d2ff;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 3px 8px;
                border-radius: 8px;
                border: 1px solid rgba(0, 210, 255, 0.3);
            }
        """)
        avatar_layout.addWidget(self.status_pill, 0, Qt.AlignHCenter)

        # Install event filters so clicks/drags anywhere on the avatar are captured reliably
        self.avatar_container.installEventFilter(self)
        self.viewport_3d.installEventFilter(self)
        self.status_pill.installEventFilter(self)

        self.main_layout.addWidget(self.avatar_container, 0, Qt.AlignHCenter)

        # ------------------- 2. COMPACT CHAT POPOVER PANEL -------------------
        self.chat_popover = QFrame(self)
        self.chat_popover.setFixedSize(self.POPOVER_WIDTH, self.POPOVER_HEIGHT)
        self.chat_popover.setStyleSheet("""
            QFrame#ChatPopover {
                background-color: rgba(13, 16, 24, 0.94);
                border: 1px solid rgba(0, 210, 255, 0.35);
                border-radius: 16px;
            }
        """)
        self.chat_popover.setObjectName("ChatPopover")

        popover_layout = QVBoxLayout(self.chat_popover)
        popover_layout.setContentsMargins(12, 10, 12, 10)
        popover_layout.setSpacing(8)

        # Popover Top Bar (Title + Minimize "×" button)
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(2, 0, 2, 0)

        title_lbl = QLabel("NOVA ASSISTANT")
        title_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffffff; letter-spacing: 1px;")
        header_bar.addWidget(title_lbl)

        header_bar.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(22, 22)
        self.btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #8fa0b5;
                font-size: 11px;
                font-weight: bold;
                border-radius: 11px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 60, 60, 0.3);
                color: #ffffff;
            }
        """)
        self.btn_close.clicked.connect(self.hide_chat_popover)
        header_bar.addWidget(self.btn_close)

        popover_layout.addLayout(header_bar)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: rgba(0, 210, 255, 0.15);")
        popover_layout.addWidget(divider)

        # Scrollable Chat History
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_widget)
        popover_layout.addWidget(self.scroll_area, 1)

        # Input Row (Field + Mic + Send)
        input_bar = QHBoxLayout()
        input_bar.setSpacing(6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("State your command...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(22, 28, 42, 0.85);
                color: #ffffff;
                font-size: 11px;
                padding: 8px 12px;
                border-radius: 10px;
                border: 1px solid rgba(0, 210, 255, 0.2);
            }
            QLineEdit:focus {
                border: 1px solid #00d2ff;
                background-color: rgba(25, 33, 50, 0.95);
            }
        """)
        self.input_field.returnPressed.connect(self._handle_send_command)
        input_bar.addWidget(self.input_field, 1)

        # Voice input button
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setFixedSize(32, 32)
        self.btn_mic.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background-color: rgba(28, 36, 54, 0.85);
                color: #a4b4c7;
                font-size: 13px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background-color: rgba(0, 210, 255, 0.2);
                border-color: #00d2ff;
            }
        """)
        self.btn_mic.clicked.connect(self._handle_voice_input)
        input_bar.addWidget(self.btn_mic)

        # Send button
        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(32, 32)
        self.btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #0099ff;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #00b4ff;
            }
            QPushButton:pressed {
                background-color: #0080d4;
            }
        """)
        self.btn_send.clicked.connect(self._handle_send_command)
        input_bar.addWidget(self.btn_send)

        popover_layout.addLayout(input_bar)
        self.main_layout.addWidget(self.chat_popover, 0, Qt.AlignHCenter)

    # ------------------- DRAG & CLICK LOGIC ON AVATAR -------------------

    def eventFilter(self, watched, event):
        """Intercept mouse events on child avatar components for smooth dragging & click detection."""
        if watched in (self.avatar_container, self.viewport_3d, self.status_pill):
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._on_avatar_press(event.globalPos(), event.pos())
                    return True
            elif event.type() == QEvent.MouseMove:
                if event.buttons() & Qt.LeftButton:
                    self._on_avatar_move(event.globalPos(), event.pos())
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._on_avatar_release()
                    return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # If clicked in the upper avatar area (not in the chat popover)
            if not self._popover_open or event.pos().y() <= self.AVATAR_SIZE:
                self._on_avatar_press(event.globalPos(), event.pos())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if not self._popover_open or event.pos().y() <= self.AVATAR_SIZE:
                self._on_avatar_move(event.globalPos(), event.pos())
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._popover_open or event.pos().y() <= self.AVATAR_SIZE:
                self._on_avatar_release()
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def _on_avatar_press(self, global_pos, local_pos):
        self._press_global_pos = global_pos
        self._press_local_pos = local_pos
        self._drag_start_offset = global_pos - self.frameGeometry().topLeft()
        self._is_dragging = False
        self._system_move_active = False
        self.avatar_container.setCursor(QCursor(Qt.ClosedHandCursor))

    def _on_avatar_move(self, global_pos, local_pos):
        if self._press_local_pos is None:
            return

        # Distance threshold (using local widget position which is accurate on Wayland & X11)
        move_dist = (local_pos - self._press_local_pos).manhattanLength()
        if move_dist > 4:
            self._is_dragging = True

            # 1. Native Wayland / modern compositor move (bypasses Wayland security coordinate limits)
            if not self._system_move_active:
                handle = self.windowHandle()
                if handle and hasattr(handle, "startSystemMove"):
                    self._system_move_active = True
                    if handle.startSystemMove():
                        return

            # 2. Traditional coordinate offset move fallback (for X11 / Windows)
            if self._drag_start_offset is not None:
                self.move(global_pos - self._drag_start_offset)

    def _on_avatar_release(self):
        self.avatar_container.setCursor(QCursor(Qt.OpenHandCursor))
        if not self._is_dragging:
            # Clean click without drag -> Toggle chat popover!
            self.toggle_chat_popover()

        self._is_dragging = False
        self._press_global_pos = None
        self._press_local_pos = None
        self._drag_start_offset = None
        self._system_move_active = False

    def changeEvent(self, event):
        """Auto-hide popover when window loses focus (clicked outside)."""
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow() and self._popover_open:
                self.hide_chat_popover()
        super().changeEvent(event)

    def keyPressEvent(self, event):
        """Allow Escape key to dismiss popover."""
        if event.key() == Qt.Key_Escape and self._popover_open:
            self.hide_chat_popover()
            event.accept()
            return
        super().keyPressEvent(event)

    # ------------------- POPOVER TOGGLING & GEOMETRY -------------------

    def toggle_chat_popover(self):
        if self._popover_open:
            self.hide_chat_popover()
        else:
            self.show_chat_popover()

    def show_chat_popover(self):
        self._popover_open = True
        self._update_geometry(popover_visible=True)
        self.input_field.setFocus()

    def hide_chat_popover(self):
        self._popover_open = False
        self._update_geometry(popover_visible=False)

    def _update_geometry(self, popover_visible: bool):
        if popover_visible:
            self.chat_popover.show()
            w = max(self.AVATAR_SIZE + 20, self.POPOVER_WIDTH + 16)
            h = self.AVATAR_SIZE + self.POPOVER_HEIGHT + 24
            self.setFixedSize(w, h)

            # Prevent popover from sliding off screen bounds
            screen = QApplication.primaryScreen()
            if screen:
                screen_geom = screen.geometry()
                curr_pos = self.pos()
                new_x = curr_pos.x()
                new_y = curr_pos.y()

                if curr_pos.y() + h > screen_geom.bottom() - 10:
                    new_y = max(screen_geom.top() + 10, screen_geom.bottom() - h - 10)
                if curr_pos.x() + w > screen_geom.right() - 10:
                    new_x = max(screen_geom.left() + 10, screen_geom.right() - w - 10)

                if new_x != curr_pos.x() or new_y != curr_pos.y():
                    self.move(new_x, new_y)
        else:
            self.chat_popover.hide()
            w = self.AVATAR_SIZE + 14
            h = self.AVATAR_SIZE + 14
            self.setFixedSize(w, h)

    def _set_status(self, text: str, color: str = "#00d2ff"):
        self.status_pill.setText(text)
        self.status_pill.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(14, 18, 28, 0.85);
                color: {color};
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 3px 8px;
                border-radius: 8px;
                border: 1px solid rgba(0, 210, 255, 0.3);
            }}
        """)

    # ------------------- CHAT & WORKER LOGIC -------------------

    def _post_user_message(self, text: str):
        bubble = CompactChatBubble("YOU", text, is_user=True)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _post_assistant_message(self, text: str, speak_now: bool = False):
        bubble = CompactChatBubble("NOVA", text, is_user=False)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

        if speak_now:
            self.viewport_3d.set_state("speaking")
            self._set_status("• SPEAKING", "#00e6ff")

            class BackgroundSpeaker(QThread):
                finished_signal = pyqtSignal()
                def __init__(self, speech_text):
                    super().__init__()
                    self.speech_text = speech_text
                def run(self):
                    speak(self.speech_text)
                    self.finished_signal.emit()

            self.speaker = BackgroundSpeaker(text)
            self.speaker.finished_signal.connect(self._on_speech_finished)
            self.speaker.start()

    def _scroll_to_bottom(self):
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def _handle_send_command(self):
        command = self.input_field.text().strip()
        if not command:
            return

        self.input_field.clear()
        self._post_user_message(command)

        if command.lower() in ["exit", "quit", "bye"]:
            self._post_assistant_message("Goodbye, Boss!")
            speak("Goodbye!")
            self.close()
            return

        # Visual state: Thinking
        self.viewport_3d.set_state("thinking")
        self._set_status("• THINKING", "#be50ff")
        self.btn_send.setEnabled(False)

        # Launch async QThread
        self.current_worker = IntentWorker(command=command, speak_output=True)
        self.current_worker.response_ready.connect(self._on_response_ready)
        self.current_worker.speech_finished.connect(self._on_speech_finished)
        self.current_worker.start()

    def _on_response_ready(self, response: str):
        self._post_assistant_message(response)
        self.viewport_3d.set_state("speaking")
        self._set_status("• SPEAKING", "#00e6ff")

    def _on_speech_finished(self):
        self.viewport_3d.set_state("idle")
        self._set_status("• IDLE", "#00d2ff")
        self.btn_send.setEnabled(True)

    def _handle_voice_input(self):
        self.viewport_3d.set_state("listening")
        self._set_status("• LISTENING", "#48dc78")
        self.btn_mic.setEnabled(False)

        self.voice_worker = VoiceInputWorker()
        self.voice_worker.recognized_text.connect(self._on_voice_recognized)
        self.voice_worker.listening_finished.connect(self._on_voice_finished)
        self.voice_worker.start()

    def _on_voice_recognized(self, text: str):
        self.input_field.setText(text)
        self._handle_send_command()

    def _on_voice_finished(self):
        self.btn_mic.setEnabled(True)
        if self.status_pill.text() == "• LISTENING":
            self.viewport_3d.set_state("idle")
            self._set_status("• IDLE", "#00d2ff")


# Backwards compatibility alias
NovaMainWindow = NovaFloatingAvatar


def launch_gui():
    """Launch NOVA as a floating desktop avatar pet widget."""
    app = QApplication(sys.argv)
    avatar = NovaFloatingAvatar()
    avatar.show()
    sys.exit(app.exec_())
