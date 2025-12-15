from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QTextEdit, QStatusBar, QMessageBox, QTabWidget,
    QLineEdit, QTableWidget, QHeaderView, QTableWidgetItem
)
from PyQt6.QtGui import QFont, QPixmap
from repository import fetch_all
import sys

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

        self.action_edit = self._make_small_button("✎") # редактирование и удаление
        self.action_delete = self._make_small_button("🗑")

        self.action_edit.hide()
        self.action_delete.hide()

        self.table.cellClicked.connect(self._show_action_buttons) # клик

        self.installEventFilter(self) # убрать редактирование и удаление

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

    # ---------- Маленькая кнопка справа ----------
    def _make_small_button(self, text):
        btn = QPushButton(text, self)
        btn.setFont(QFont("AG_CenturyOldStyle", 16))
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                width: 40px;
                height: 33px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)
        return btn

    def _show_action_buttons(self, row, col):
        header_h = self.table.horizontalHeader().height()

        y = self.table.y() + header_h + sum(self.table.rowHeight(r) for r in range(row))
        y_center = y + self.table.rowHeight(row) // 2 - 15

        x_pos = self.table.x() + self.table.width() + 1

        self.action_edit.move(x_pos, y_center)
        self.action_delete.move(x_pos + 40, y_center)

        self.action_edit.show()
        self.action_delete.show()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            pos = event.position().toPoint()
            widget = self.childAt(pos)

            if widget not in (self.action_edit, self.action_delete):
                self.action_edit.hide()
                self.action_delete.hide()

        return super().eventFilter(obj, event)

class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ===== Ваши прежние настройки =====
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

        # КНИГИ
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
