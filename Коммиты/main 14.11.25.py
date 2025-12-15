from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QTextEdit, QStatusBar, QMessageBox, QVBoxLayout, QTabWidget, QLineEdit, QTableWidget,
    QHeaderView, QTableWidgetItem
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import QRect, Qt
import sys


# ====== ОКНО АДМИНА (пока заглушка) ======
class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Admin Panel")
        self.setGeometry(0, 0, 1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")
# Центральный виджет
        central = QWidget(self)
        self.setCentralWidget(central)

        # TabWidget
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

        # ===== Tabs =====
        self.page_books = self.create_books_page()
        self.page_readers = self.create_page("Страница: Читатели")
        self.page_librarians = self.create_page("Страница: Библиотекари")
        self.page_rooms = self.create_page("Страница: Залы")
        self.page_reports = self.create_page("Страница: Отчеты")

        # Добавляем вкладки
        self.tabs.addTab(self.page_books, "Книги")
        self.tabs.addTab(self.page_readers, "Читатели")
        self.tabs.addTab(self.page_librarians, "Библиотекари")
        self.tabs.addTab(self.page_rooms, "Залы")
        self.tabs.addTab(self.page_reports, "Отчеты")

    def create_page(self, text: str) -> QWidget:
        """Создание простой страницы с заголовком (потом можно наполнять)."""
        _ = self
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setFont(QFont("AG_CenturyOldStyle", 25))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: rgb(27, 71, 93);")
        layout.addWidget(label)
        return page

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            # Куда был клик
            pos = event.position().toPoint()

            # Определяем на какой вкладке мы сейчас
            current_page = self.tabs.currentWidget()

            # Виджет, по которому кликнули
            widget = current_page.childAt(pos)

            # Если кнопки существуют
            if hasattr(self, "action_edit"):
                # прячем если клик не по таблице и не по кнопкам
                if widget not in (self.action_edit, self.action_delete):
                    self.action_edit.hide()
                    self.action_delete.hide()

        return super().eventFilter(obj, event)

    def create_books_page(self):
        page = QWidget()

        # ===== Поле поиска =====
        search_input = QLineEdit(page)
        search_input.setPlaceholderText("Поиск книги...")
        search_input.setFont(QFont("AG_CenturyOldStyle", 18))
        search_input.setStyleSheet("""
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
        search_input.setGeometry(230, 25, 600, 50)  # x, y, width, height

        # ===== Кнопка "Добавить" =====
        btn_add = QPushButton("Добавить", page)
        btn_add.setFont(QFont("AG_CenturyOldStyle", 20))
        btn_add.setStyleSheet("""
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
        btn_add.setGeometry(935, 80, 160, 50)

        # ===== Кнопка "Удалить" =====
        btn_delete = QPushButton("+Автор", page)
        btn_delete.setFont(QFont("AG_CenturyOldStyle", 20))
        btn_delete.setStyleSheet("""
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
        btn_delete.setGeometry(935, 150, 160, 50)

        book_label = QLabel("Книги", page)
        book_label.setGeometry(QRect(0, 50, 131,30))
        book_label.setFont(QFont("AG_CenturyOldStyle", 18))
        book_label.setStyleSheet("color: rgb(27, 71, 93);")

        book_label = QLabel("Количество книг", page)
        book_label.setGeometry(QRect(920, 230, 300,30))
        book_label.setFont(QFont("AG_CenturyOldStyle", 18))
        book_label.setStyleSheet("color: rgb(27, 71, 93);")

        book_label = QLabel("Число", page)
        book_label.setGeometry(QRect(990, 280, 131,30))
        book_label.setFont(QFont("AG_CenturyOldStyle", 16))
        book_label.setStyleSheet("color: rgb(27, 71, 93);")

        # ===== Таблица =====
        table = QTableWidget(page)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Название", "Автор", "Год"])
        table.setStyleSheet("""
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

        # Пример данных
        data = [
            (1, "Три мушкетёра", "А. Дюма", 1844),
            (2, "Преступление и наказание", "Ф. Достоевский", 1866),
            (3, "Мастер и Маргарита", "М. Булгаков", 1967)
        ]

        table.setRowCount(len(data))
        for row, (id_, name, author, year) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(str(id_)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, QTableWidgetItem(author))
            table.setItem(row, 3, QTableWidgetItem(str(year)))

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Позиция таблицы: снизу слева
        table.setGeometry(0, 80, 830, 595)  # x, y, w, h
        page.installEventFilter(self)

        # ===== КНОПКИ СПРАВА =====
        self.action_edit = QPushButton("✎", page)
        self.action_delete = QPushButton("🗑", page)

        for btn in (self.action_edit, self.action_delete):
            btn.setFont(QFont("AG_CenturyOldStyle", 16))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(179, 195, 208);
                    border: none;
                    width: 40px;
                    height: 33px;
                    color: rgb(255, 255, 255);
                }
                QPushButton:hover {
                    background-color: rgb(200, 210, 220);
                }
            """)
            btn.hide()

        # ===== ПОКАЗ КНОПОК ПРИ НАЖАТИИ НА СТРОКУ =====
        def show_buttons(row, col):
            header_height = table.horizontalHeader().height()

            # абсолютная позиция строки внутри страницы
            y = table.y() + header_height + sum(table.rowHeight(r) for r in range(row))

            # центр строки
            y_center = y + table.rowHeight(row) // 2 - 15

            # позиция кнопок
            x_pos = table.x() + table.width() + 1

            self.action_edit.move(x_pos, y_center)
            self.action_delete.move(x_pos + 40, y_center)

            self.action_edit.show()
            self.action_delete.show()

        table.cellClicked.connect(show_buttons)

        def eventFilter(self, obj, event):
            if event.type() == event.Type.MouseButtonPress:
                # Куда был клик
                pos = event.position().toPoint()

                # Определяем на какой вкладке мы сейчас
                current_page = self.tabs.currentWidget()

                # Виджет, по которому кликнули
                widget = current_page.childAt(pos)

                # Если кнопки существуют
                if hasattr(self, "action_edit"):
                    # прячем если клик не по таблице и не по кнопкам
                    if widget not in (self.action_edit, self.action_delete):
                        self.action_edit.hide()
                        self.action_delete.hide()

            return super().eventFilter(obj, event)

        # ===== СКРЫТИЕ КНОПОК ПРИ КЛИКЕ В ЛЮБОЕ МЕСТО =====
        def hide_buttons(event):
            # Проверяем, не внутри ли таблицы был клик
            if not table.geometry().contains(event.pos()):
                self.action_edit.hide()
                self.action_delete.hide()
            return super(QWidget, page).eventFilter(self, event)

        page.event = hide_buttons

        return page


# ====== ОКНО ЛОГИНА ======
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MainWindow")
        self.setGeometry(0, 0, 1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # ===== Поля логина =====
        self.login_edit = QTextEdit(self.centralwidget)
        self.login_edit.setGeometry(QRect(810, 250, 321, 41))
        self.login_edit.setFont(QFont("AG_CenturyOldStyle", 18))
        self.login_edit.setStyleSheet("""
            background-color: rgb(179, 195, 208);
            border: none;
            color: rgb(27, 71, 93);
        """)

        self.login_label = QLabel("Логин", self.centralwidget)
        self.login_label.setGeometry(QRect(560, 240, 131, 51))
        self.login_label.setFont(QFont("AG_CenturyOldStyle", 28))
        self.login_label.setStyleSheet("color: rgb(27, 71, 93);")

        # ===== Поле пароля =====
        self.password_edit = QTextEdit(self.centralwidget)
        self.password_edit.setGeometry(QRect(810, 340, 321, 41))
        self.password_edit.setFont(QFont("AG_CenturyOldStyle", 18))
        self.password_edit.setStyleSheet("""
            background-color: rgb(179, 195, 208);
            border: none;
            color: rgb(27, 71, 93);
        """)

        self.password_label = QLabel("Пароль", self.centralwidget)
        self.password_label.setGeometry(QRect(560, 330, 161, 61))
        self.password_label.setFont(QFont("AG_CenturyOldStyle", 28))
        self.password_label.setStyleSheet("color: rgb(27, 71, 93);")

        # ===== Кнопка =====
        self.entrance_button = QPushButton("Войти", self.centralwidget)
        self.entrance_button.setGeometry(QRect(660, 440, 221, 91))
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
        self.entrance_label.setGeometry(QRect(670, 100, 221, 101))
        self.entrance_label.setFont(QFont("AG_CenturyOldStyle", 48))
        self.entrance_label.setStyleSheet("color: rgb(27, 71, 93);")

        # ===== Картинка =====
        self.image_label = QLabel(self.centralwidget)
        self.image_label.setGeometry(QRect(60, 120, 411, 421))
        self.image_label.setPixmap(QPixmap("result_девочки (2).png"))
        self.image_label.setScaledContents(True)

        # ===== Статусбар =====
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # Окно администратора создаём заранее
        self.admin_window = AdminWindow()

    # ===== Проверка логина =====
    def try_login(self):
        login = self.login_edit.toPlainText().strip()
        password = self.password_edit.toPlainText().strip()

        if login == "admin" and password == "123456":
            self.admin_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")


# ===== Точка входа =====
def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
