from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QWidget, QScrollArea
)
from PyQt6.QtCore import Qt


class RecordDialog(QDialog):
    def __init__(
        self,
        columns: list[str],
        save_callback,
        values: dict | None = None,
        hidden_fields: list[str] | None = None,
        close_on_save: bool = False
    ):
        super().__init__()

        self.columns = columns
        self.save_callback = save_callback
        self.values = values or {}
        self.hidden_fields = hidden_fields or []
        self.close_on_save = close_on_save
        self.inputs: dict[str, QLineEdit] = {}

        # ===== Режим =====
        self.is_edit_mode = bool(values)
        self.setWindowTitle("Редактирование" if self.is_edit_mode else "Добавление")

        # ===== Окно =====
        self.resize(750, 520)
        self.setMinimumSize(650, 450)

        self.setStyleSheet("""
            QDialog {
                background-color: rgb(248, 242, 239);
            }
        """)

        # ===== Главный layout =====
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 20)
        main_layout.setSpacing(20)

        # ===== Заголовок =====
        title = QLabel("Редактирование" if self.is_edit_mode else "Добавление")
        title.setStyleSheet("""
            QLabel {
                color: rgb(27, 71, 93);
                font-size: 22px;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(title)

        # ===== Прокручиваемая форма =====
        form_widget = QWidget()
        form_widget.setStyleSheet("""
            QWidget {
                background-color: rgb(248, 242, 239);
            }
        """)

        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)

        for col in columns:
            if col in self.hidden_fields:
                continue

            label = QLabel(col)
            label.setStyleSheet("""
                QLabel {
                    color: rgb(27, 71, 93);
                    font-size: 14px;
                }
            """)

            edit = QLineEdit()
            edit.setMinimumHeight(36)
            edit.setStyleSheet("""
                QLineEdit {
                    background-color: rgb(179, 195, 208);
                    border: none;
                    border-radius: 8px;
                    padding-left: 10px;
                    color: rgb(27, 71, 93);
                    font-size: 14px;
                }
            """)

            # === Заполнение при редактировании ===
            if col in self.values and self.values[col] is not None:
                edit.setText(str(self.values[col]))

            self.inputs[col] = edit
            form_layout.addWidget(label)
            form_layout.addWidget(edit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: rgb(248, 242, 239);
            }
            QScrollArea QWidget {
                background-color: rgb(248, 242, 239);
            }
        """)

        main_layout.addWidget(scroll)

        # ===== Кнопки =====
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        self.save_btn = QPushButton("Сохранить")
        self.close_btn = QPushButton("Закрыть")

        for btn in (self.save_btn, self.close_btn):
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(140)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(179, 195, 208);
                    border: none;
                    color: rgb(27, 71, 93);
                    border-radius: 20px;
                    padding: 6px 12px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: rgb(200, 210, 220);
                }
            """)

        buttons_layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(buttons_layout)

        # ===== Сигналы =====
        self.save_btn.clicked.connect(self.on_save)
        self.close_btn.clicked.connect(self.close)

    # ===== Логика сохранения =====
    def on_save(self):
        values = {
            col: edit.text() if edit.text() != "" else None
            for col, edit in self.inputs.items()
        }

        self.save_callback(values)

        if self.close_on_save:
            self.close()
        else:
            self.clear_fields()

    def clear_fields(self):
        for edit in self.inputs.values():
            edit.clear()

class ConfirmDeleteDialog(QDialog):
    def __init__(self, confirm_callback):
        super().__init__()
        self.confirm_callback = confirm_callback
        self.setWindowTitle("Удаление записи")
        self.resize(400, 150)
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(248, 242, 239);
            }
            QLabel {
                color: rgb(27, 71, 93);
                font-size: 16px;
            }
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Сообщение
        message = QLabel("Вы действительно хотите удалить выбранную запись?")
        message.setWordWrap(True)
        layout.addWidget(message, alignment=Qt.AlignmentFlag.AlignCenter)

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Удалить")
        self.cancel_btn = QPushButton("Отмена")

        self.delete_btn.clicked.connect(self.on_delete)
        self.cancel_btn.clicked.connect(self.close)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

    def on_delete(self):
        self.confirm_callback()
        self.close()