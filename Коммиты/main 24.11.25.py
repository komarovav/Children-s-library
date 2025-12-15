from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QTextEdit, QStatusBar, QMessageBox, QTabWidget,
    QLineEdit, QTableWidget, QHeaderView, QTableWidgetItem
)
from PyQt6.QtGui import QFont, QPixmap
from repository import fetch_all, insert_row, update_row, delete_row
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox)

class RecordDialog(QDialog):
    def __init__(self, columns, data=None):
        super().__init__()
        self.setWindowTitle("Редактирование записи" if data else "Добавление записи")
        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.inputs = {}
        for col, val in zip(columns, data if data else [""]*len(columns)):
            line_edit = QLineEdit(str(val))
            self.inputs[col] = line_edit
            self.form_layout.addRow(col, line_edit)

        self.layout.addLayout(self.form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def get_data(self):
        return {col: self.inputs[col].text() for col in self.inputs}


# ---------- Диалог для удаления ----------
class DeleteDialog(QDialog):
    def __init__(self, record):
        super().__init__()
        self.setWindowTitle("Удаление записи")
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(f"Вы точно хотите удалить запись?\n{record}"))

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)
class PageTemplate(QWidget): # шаблон для страниц
    """
    Шаблонная страница:
    - Поле поиска
    - Две верхние кнопки
    - Заголовок
    - Таблица
    - Правые всплывающие кнопки редактирования/удаления
    """

    def __init__(self, title: str, columns: list[str], data: list[tuple]):
        super().__init__()

        self.search_input = QLineEdit(self) # поиск
        self.search_input.setPlaceholderText(f"Поиск: {title.lower()}...")
        self.search_input.setFont(QFont("AG_CenturyOldStyle", 18))
        self.search_input.setGeometry(230, 25, 600, 50)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                padding: 10px;
                border-radius: 15px;
                color: rgb(27, 71, 93);
            }
            QLineEdit::placeholder {
                color: rgb(27, 71, 93);
            }
        """)

        self.btn_add = self._make_main_button("Добавить", 935, 80) # добавить
        self.btn_upd = self._make_main_button("Редактировать", 935, 200)
        self.btn_del = self._make_main_button("Удалить", 935, 400)

        label = QLabel(title, self) # заголовок
        label.setFont(QFont("AG_CenturyOldStyle", 18))
        label.setStyleSheet("color: rgb(27, 71, 93);")
        label.setGeometry(0, 48, 200, 40)

        self.table = QTableWidget(self) # таблица
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setGeometry(0, 80, 830, 595)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: rgb(27, 71, 93);
                border: 2px solid rgb(179, 195, 208);
                border-radius: 10px;
                gridline-color: rgb(179, 195, 208);
            }
            QHeaderView::section {
                background-color: rgb(179, 195, 208);
                color: rgb(27, 71, 93);
                padding: 5px;
                font-size: 18px;
            }
            QTableWidget::item {
                padding: 10px;
            }
        """)

        # Загружаем данные
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    # ---------- Создание большой кнопки ----------
    def _make_main_button(self, text, x, y):
        btn = QPushButton(text, self)
        btn.setFont(QFont("AG_CenturyOldStyle", 20))
        btn.setGeometry(x, y, 160, 50)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 15px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)
        return btn

    def setup_actions(self, table_name):
        # Кнопка добавления
        self.btn_add.clicked.connect(lambda: self.add_record(table_name))
        self.btn_upd.clicked.connect(lambda: self.edit_record(table_name))
        self.btn_del.clicked.connect(lambda: self.delete_record(table_name))

    def add_record(self, table_name):
        dialog = RecordDialog(self.table.horizontalHeaderLabels())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                insert_row(table_name, data)
                self.refresh_table(table_name)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись:\n{e}")

    def edit_record(self, table_name):
        selected = self.table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите строку для редактирования")
            return
        current_data = [self.table.item(selected, i).text() for i in range(self.table.columnCount())]
        dialog = RecordDialog(self.table.horizontalHeaderLabels(), current_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            key = self.table.item(selected, 0).text()
            try:
                update_row(table_name, key, data)
                self.refresh_table(table_name)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись:\n{e}")

    def delete_record(self, table_name):
        selected = self.table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите строку для удаления")
            return
        record = [self.table.item(selected, i).text() for i in range(self.table.columnCount())]
        dialog = DeleteDialog(record)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            key = record[0]
            try:
                delete_row(table_name, key)
                self.refresh_table(table_name)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись:\n{e}")

    def refresh_table(self, table_name):
        data, cols = fetch_all(table_name)
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))


class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Admin Panel")
        self.setGeometry(0, 0, 1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        central = QWidget(self)
        self.setCentralWidget(central)

        self.tabs = QTabWidget(central)
        self.tabs.setGeometry(0, 0, 1200, 700)
        self.tabs.setFont(QFont("AG_CenturyOldStyle", 25))

        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: rgb(179, 195, 208);
                color: rgb(27, 71, 93);
                padding: 15px;
                width: 210px;
            }
            QTabBar::tab:selected {
                background: rgb(248, 242, 239);
                color: rgb(27, 71, 93);
            }
        """)

        # ===== Загружаем таблицы из БД =====
        books, books_cols = fetch_all("books")
        readers, readers_cols = fetch_all("readers")
        librarians, librarians_cols = fetch_all("librarians")
        hall, hall_cols = fetch_all("hall")

        # ===== Формируем страницы =====
        page_books = PageTemplate(
            title="Книги",
            columns=books_cols,
            data=[tuple(r[c] for c in books_cols) for r in books]
        )

        page_readers = PageTemplate(
            title="Читатели",
            columns=readers_cols,
            data=[tuple(r[c] for c in readers_cols) for r in readers]
        )

        page_librarians = PageTemplate(
            title="Библиотекари",
            columns=librarians_cols,
            data=[tuple(r[c] for c in librarians_cols) for r in librarians]
        )

        page_rooms = PageTemplate(
            title="Залы",
            columns=hall_cols,
            data=[tuple(r[c] for c in hall_cols) for r in hall]
        )

        # ===== Настройка действий кнопок =====
        page_books.setup_actions("books")
        page_readers.setup_actions("readers")
        page_librarians.setup_actions("librarians")
        page_rooms.setup_actions("hall")

        # ===== Добавляем вкладки =====
        self.tabs.addTab(page_books, "Книги")
        self.tabs.addTab(page_readers, "Читатели")
        self.tabs.addTab(page_librarians, "Библиотекари")
        self.tabs.addTab(page_rooms, "Залы")

class LoginWindow(QMainWindow): # логин
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MainWindow")
        self.setGeometry(0, 0, 1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # ===== Логин =====
        self.login_edit = QTextEdit(self.centralwidget)
        self.login_edit.setGeometry(810, 250, 321, 41)
        self.login_edit.setFont(QFont("AG_CenturyOldStyle", 18))
        self.login_edit.setStyleSheet("""
            background-color: rgb(179, 195, 208);
            border: none;
            color: rgb(27, 71, 93);
        """)

        self.login_label = QLabel("Логин", self.centralwidget)
        self.login_label.setGeometry(560, 240, 131, 51)
        self.login_label.setFont(QFont("AG_CenturyOldStyle", 28))
        self.login_label.setStyleSheet("color: rgb(27, 71, 93);")

        # ===== Пароль =====
        self.password_edit = QTextEdit(self.centralwidget)
        self.password_edit.setGeometry(810, 340, 321, 41)
        self.password_edit.setFont(QFont("AG_CenturyOldStyle", 18))
        self.password_edit.setStyleSheet("""
            background-color: rgb(179, 195, 208);
            border: none;
            color: rgb(27, 71, 93);
        """)

        self.password_label = QLabel("Пароль", self.centralwidget)
        self.password_label.setGeometry(560, 330, 161, 61)
        self.password_label.setFont(QFont("AG_CenturyOldStyle", 28))
        self.password_label.setStyleSheet("color: rgb(27, 71, 93);")

        # ===== Кнопка входа =====
        self.entrance_button = QPushButton("Войти", self.centralwidget)
        self.entrance_button.setGeometry(660, 440, 221, 91)
        self.entrance_button.setFont(QFont("AG_CenturyOldStyle", 20))
        self.entrance_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 20px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)
        self.entrance_button.clicked.connect(self.try_login)

        # ===== Заголовок =====
        self.entrance_label = QLabel("ВХОД", self.centralwidget)
        self.entrance_label.setGeometry(670, 100, 221, 101)
        self.entrance_label.setFont(QFont("AG_CenturyOldStyle", 48))
        self.entrance_label.setStyleSheet("color: rgb(27, 71, 93);")

        # ===== Картинка =====
        self.image_label = QLabel(self.centralwidget)
        self.image_label.setGeometry(60, 120, 411, 421)
        self.image_label.setPixmap(QPixmap("result_девочки (2).png"))
        self.image_label.setScaledContents(True)

        # ===== Статус =====
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # Окно администратора
        self.admin_window = AdminWindow()

    def try_login(self):
        login = self.login_edit.toPlainText().strip()
        password = self.password_edit.toPlainText().strip()

        if login == "admin" and password == "123456":
            self.admin_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
