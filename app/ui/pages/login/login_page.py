"""Login view with a responsive 55/45 form and artwork split."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from app.ui.widgets.app_input import AppInput
from app.ui.widgets.buttons import PrimaryButton
from app.ui.widgets.cover_image import CoverImage
from app.ui.widgets.google_button import GoogleButton
from app.ui.widgets.password_input import LoginPasswordInput
from app.ui.widgets.text_link import TextLink
from app.ui.widgets.toast import Toast

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"
_IMAGES = Path(__file__).resolve().parents[3] / "assets/images"


class LoginPage(QWidget):
    login_requested = Signal(str, str, bool)
    back_requested = Signal()
    forgot_requested = Signal()
    google_requested = Signal()
    admin_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("loginPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName("loginContainer")
        container_row = QHBoxLayout(container)
        container_row.setContentsMargins(0, 0, 0, 0)
        container_row.setSpacing(0)

        container_row.addWidget(self._build_form_panel(), 55)

        self.artwork = CoverImage(str(_IMAGES / "login_artwork.png"), mode="contain")
        self.artwork.setObjectName("loginArtworkPanel")
        self.artwork.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container_row.addWidget(self.artwork, 45)

        outer.addWidget(container)

        self.back_button.clicked.connect(self.back_requested.emit)
        self.submit.clicked.connect(self._submit)
        self.password.returnPressed.connect(self._submit)
        self.identifier.returnPressed.connect(self.password.setFocus)
        self.forgot.clicked.connect(self.forgot_requested.emit)
        self.google.clicked.connect(self.google_requested.emit)
        self.admin.clicked.connect(self.admin_requested.emit)
        self._loading = False

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("loginFormPanel")
        panel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        panel_layout = QHBoxLayout(panel)
        panel_layout.setContentsMargins(40, 24, 40, 24)
        form = QWidget()
        form.setObjectName("loginForm")
        form.setMaximumWidth(560)
        form.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        panel_layout.addWidget(form)
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column = QVBoxLayout(form)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)

        self.back_button = TextLink("Quay lại", QIcon(str(_ICONS / "arrow_left.svg")))
        self.back_button.setObjectName("loginBack")
        column.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        column.addSpacing(28)

        title = QLabel("Đăng nhập")
        title.setObjectName("loginTitle")
        column.addWidget(title)
        column.addSpacing(4)

        greeting = QLabel("Chào mừng bạn trở lại! ♥")
        greeting.setObjectName("loginGreeting")
        column.addWidget(greeting)
        column.addSpacing(18)

        self.toast = Toast(plain=True)
        column.addWidget(self.toast)

        self.identifier = AppInput("Email hoặc tên tài khoản", "user.svg")
        self.identifier.setObjectName("loginEmailInput")
        column.addWidget(self.identifier)
        column.addSpacing(10)

        self.password = LoginPasswordInput("Mật khẩu")
        self.password.setObjectName("loginPasswordInput")
        column.addWidget(self.password)
        column.addSpacing(10)

        options = QHBoxLayout()
        self.remember = QCheckBox("Ghi nhớ đăng nhập")
        self.remember.setObjectName("loginRemember")
        self.forgot = TextLink("Quên mật khẩu?")
        self.forgot.setObjectName("loginForgot")
        options.addWidget(self.remember)
        options.addStretch(1)
        options.addWidget(self.forgot)
        column.addLayout(options)
        column.addSpacing(12)

        self.submit = PrimaryButton("Đăng nhập")
        self.submit.setObjectName("loginSubmit")
        column.addWidget(self.submit)
        column.addSpacing(15)

        divider = QHBoxLayout()
        divider.setSpacing(8)
        left_line = QFrame()
        left_line.setObjectName("loginDivider")
        left_line.setFixedHeight(1)
        or_label = QLabel("hoặc")
        or_label.setObjectName("loginOr")
        right_line = QFrame()
        right_line.setObjectName("loginDivider")
        right_line.setFixedHeight(1)
        divider.addWidget(left_line, 1)
        divider.addWidget(or_label)
        divider.addWidget(right_line, 1)
        column.addLayout(divider)
        column.addSpacing(12)

        self.google = GoogleButton("Đăng nhập với Google")
        self.google.setObjectName("loginGoogle")
        column.addWidget(self.google)
        column.addSpacing(28)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        bottom.addStretch(1)
        no_account = QLabel("Chưa có tài khoản?")
        no_account.setObjectName("loginMuted")
        bottom.addWidget(no_account)
        self.admin = TextLink("Liên hệ Admin")
        self.admin.setObjectName("loginAdmin")
        bottom.addWidget(self.admin)
        bottom.addStretch(1)
        column.addLayout(bottom)

        return panel

    def _submit(self) -> None:
        if not self._loading:
            self.login_requested.emit(self.identifier.text(), self.password.text(), self.remember.isChecked())

    def set_loading(self, loading: bool) -> None:
        self._loading = loading
        self.submit.set_loading(loading, "Đang đăng nhập…")
        for widget in (
            self.identifier,
            self.password,
            self.remember,
            self.back_button,
            self.forgot,
            self.google,
            self.admin,
        ):
            widget.setEnabled(not loading)
