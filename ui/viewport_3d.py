import math
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class Model3DViewport(QWidget):
    """
    Dedicated viewport for the 3D model / avatar representation.
    
    Supports transparent floating desktop avatar mode or container embedding.
    Renders a responsive, holographic AI core with animated status pulses:
    - 'idle': Soft Cyan
    - 'listening': Calm Green
    - 'thinking': Deep Purple
    - 'speaking': Bright Cyan
    
    Exposes clean extension hooks to load full 3D assets (glTF / .glb / OBJ).
    """

    STATE_COLORS = {
        "idle": QColor(0, 180, 255),       # Soft Cyan
        "listening": QColor(72, 220, 120),  # Calm Green
        "thinking": QColor(190, 80, 255),   # Deep Purple
        "speaking": QColor(0, 230, 255),    # Bright Cyan
    }

    def __init__(self, parent=None, transparent_bg: bool = True, compact: bool = True):
        super().__init__(parent)
        self.transparent_bg = transparent_bg
        self.compact = compact
        self.state = "idle"
        self.angle = 0.0
        self.pulse = 1.0
        self.pulse_dir = 0.02
        self.model_loaded_text = ""

        # Sizing defaults for floating desktop pet
        self.setMinimumSize(160, 160)

        # Animation timer (approx 30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(33)

        if not self.compact:
            layout = QVBoxLayout(self)
            layout.addStretch()
            self.lbl_title = QLabel("3D MODEL VIEWPORT", self)
            self.lbl_title.setAlignment(Qt.AlignCenter)
            self.lbl_title.setStyleSheet("color: #798da3; font-weight: bold; font-size: 11px; letter-spacing: 2px;")
            layout.addWidget(self.lbl_title)

            self.lbl_sub = QLabel("Slot reserved for 3D model integration", self)
            self.lbl_sub.setAlignment(Qt.AlignCenter)
            self.lbl_sub.setStyleSheet("color: #485668; font-size: 10px;")
            layout.addWidget(self.lbl_sub)

    def set_state(self, state: str):
        """Update animation mood based on assistant activity."""
        if state in self.STATE_COLORS:
            self.state = state
            self.update()

    def load_3d_model(self, model_path: str):
        """
        Placeholder method for loading a future 3D model asset (.glb / glTF / OBJ).
        Ready to connect to a 3D loader or OpenGL viewport initialization.
        """
        self.model_loaded_text = model_path
        if hasattr(self, 'lbl_sub'):
            self.lbl_sub.setText(f"Loaded: {model_path}")
        self.update()

    def _animate(self):
        self.angle = (self.angle + 1.5) % 360
        self.pulse += self.pulse_dir
        if self.pulse > 1.15:
            self.pulse_dir = -0.015
        elif self.pulse < 0.95:
            self.pulse_dir = 0.015
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Optional solid background if not in transparent mode
        if not self.transparent_bg:
            painter.fillRect(self.rect(), QColor(14, 16, 24))

        base_color = self.STATE_COLORS.get(self.state, QColor(0, 180, 255))
        min_dim = min(w, h)
        core_radius = (min_dim * 0.26) * self.pulse

        # 0. Subtle translucent circular glass backing (ensures visibility on any wallpaper)
        glass_grad = QRadialGradient(cx, cy, core_radius * 1.8)
        glass_grad.setColorAt(0.0, QColor(10, 14, 22, 170))
        glass_grad.setColorAt(0.8, QColor(8, 12, 18, 110))
        glass_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glass_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - core_radius * 1.8, cy - core_radius * 1.8, core_radius * 3.6, core_radius * 3.6))

        # 1. Holographic outer glow
        outer_grad = QRadialGradient(cx, cy, core_radius * 2.2)
        outer_grad.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 55))
        outer_grad.setColorAt(0.7, QColor(base_color.red(), base_color.green(), base_color.blue(), 15))
        outer_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(outer_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - core_radius * 2.2, cy - core_radius * 2.2, core_radius * 4.4, core_radius * 4.4))

        # 2. Orbital holographic rings
        pen_ring = QPen(QColor(base_color.red(), base_color.green(), base_color.blue(), 110))
        pen_ring.setWidth(2)
        pen_ring.setStyle(Qt.DashLine)
        painter.setPen(pen_ring)
        painter.setBrush(Qt.NoBrush)

        ring1_r = core_radius * 1.45
        painter.drawEllipse(QRectF(cx - ring1_r, cy - ring1_r * 0.45, ring1_r * 2, ring1_r * 0.9))

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        painter.drawEllipse(QRectF(-ring1_r * 0.85, -ring1_r * 0.85 * 0.4, ring1_r * 1.7, ring1_r * 0.8))
        painter.restore()

        # 3. Inner pulsing core
        core_grad = QRadialGradient(cx, cy, core_radius)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
        core_grad.setColorAt(0.3, QColor(base_color.red(), base_color.green(), base_color.blue(), 210))
        core_grad.setColorAt(0.8, QColor(base_color.red(), base_color.green(), base_color.blue(), 90))
        core_grad.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - core_radius, cy - core_radius, core_radius * 2, core_radius * 2))

        # 4. Central NOVA emblem
        painter.setPen(QColor(10, 14, 20))
        font_size = max(8, int(min_dim * 0.055))
        font = QFont("Arial", font_size, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(cx - 30, cy - 10, 60, 20), Qt.AlignCenter, "NOVA")
