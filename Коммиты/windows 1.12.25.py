from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QTabWidget, QStatusBar, QMessageBox
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget,
    QPushButton, QTableWidgetItem
)
from pages import PageTemplate
from repository import fetch_all, insert_row, update_row, delete_row
class AuthorsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторы")
        self.setFixedSize(700, 500)

        self.table_name = "authors"
        self.primary_key = "id_автора"

        layout = QVBoxLayout(self)

        # Таблица
        self.table = QTableWidget(self)
        self.table.setFont(QFont("AG_CenturyOldStyle", 14))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid rgb(179, 195, 208);
                color: rgb(27, 71, 93);
            }
            QHeaderView::section {
                background-color: rgb(179, 195, 208);
                color: rgb(27, 71, 93);
                padding: 5px;
            }
        """)
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Удалить")
        self.btn_save = QPushButton("Сохранить")
        for btn in (self.btn_delete, self.btn_save):
            btn.setFont(QFont("AG_CenturyOldStyle", 14))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(179, 195, 208);
                    border: none;
                    border-radius: 8px;
                    padding: 6px 12px;
                    color: rgb(27, 71, 93);
                }
                QPushButton:hover {
                    background-color: rgb(200, 210, 220);
                }
            """)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        self.btn_delete.clicked.connect(self.delete_row)
        self.btn_save.clicked.connect(self.save_changes)

        self.load_data()

    def load_data(self):
        rows, columns = fetch_all(self.table_name)
        self.columns = columns
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(rows) + 1)  # добавляем пустую строку внизу

        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    def save_changes(self):
        pk_index = self.columns.index(self.primary_key)
        for row in range(self.table.rowCount()):
            values = {}
            pk_item = self.table.item(row, pk_index)
            for c, col_name in enumerate(self.columns):
                if col_name == self.primary_key:
                    continue
                item = self.table.item(row, c)
                text = item.text().strip() if item else ""
                values[col_name] = text if text != "" else None

            if all(v is None for v in values.values()):
                continue

            if not pk_item or not pk_item.text().strip():
                insert_row(self.table_name, values)
            else:
                update_row(self.table_name, pk_item.text(), values, self.primary_key)

        QMessageBox.information(self, "Готово", "Изменения сохранены")
        self.load_data()

    def delete_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите строку")
            return

        pk_index = self.columns.index(self.primary_key)
        pk_item = self.table.item(row, pk_index)
        if not pk_item or not pk_item.text():
            self.table.removeRow(row)
            return

        delete_row(self.table_name, pk_item.text(), self.primary_key)
        self.load_data()

class ReportPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        # Заголовок
        self.title_label = QLabel("Отчет", self)
        self.title_label.setGeometry(0, 48, 200, 40)
        self.title_label.setFont(QFont("AG_CenturyOldStyle", 18))
        self.title_label.setStyleSheet("color: rgb(27, 71, 93);")

        label_role = QLabel("Администратор", self)
        label_role.setFont(QFont("AG_CenturyOldStyle", 18))
        label_role.setStyleSheet("color: rgb(27, 71, 93);")
        label_role.setGeometry(1015, 595, 200, 40)

        # Поле вывода отчёта
        self.report_output = QTextEdit(self)
        self.report_output.setGeometry(0, 80, 870, 595)
        self.report_output.setFont(QFont("AG_CenturyOldStyle", 16))
        self.report_output.setReadOnly(True)
        self.report_output.setStyleSheet("""
            background-color: white;
            border: 2px solid rgb(179, 195, 208);
            color: rgb(27, 71, 93);
            padding: 10px;
        """)

        # Кнопка "Вывести"
        self.show_button = QPushButton("Вывести", self)
        self.show_button.setGeometry(955, 80, 160, 50)
        self.show_button.setFont(QFont("AG_CenturyOldStyle", 16))
        self.show_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)

        self.show_button.clicked.connect(self.show_report)

    def show_report(self):
        # Заглушка — логика будет добавлена позже
        self.report_output.setText(
            "Список читателей, не вернувших книги в срок:\n\n"
            "1. Иванов Иван Иванович\n"
            "   Телефон: +7 (900) 000-00-00\n"
            "   Email: ivanov@example.com\n\n"
            "2. Петрова Анна Сергеевна\n"
            "   Телефон: +7 (900) 111-11-11\n"
            "   Email: petrova@example.com"
        )

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

        books, books_cols = fetch_all("books")
        readers, readers_cols = fetch_all("readers")
        librarians, librarians_cols = fetch_all("librarians")
        hall, hall_cols = fetch_all("hall")

        page_books = PageTemplate(
            title="Книги",
            columns=books_cols,
            data=books,
            table_name="books",
            primary_key="id_книги"
        )

        page_readers = PageTemplate(
            title="Читатели",
            columns=readers_cols,
            data=readers,
            table_name="readers",
            primary_key="id_читателя"
        )

        page_librarians = PageTemplate(
            title="Библиотекари",
            columns=librarians_cols,
            data=librarians,
            table_name="librarians",
            primary_key="id_библиотекаря"
        )

        page_rooms = PageTemplate(
            title="Залы",
            columns=hall_cols,
            data=hall,
            table_name="hall",
            primary_key="id_зала"
        )

        self.tabs.addTab(page_books, "Книги")
        self.tabs.addTab(page_readers, "Читатели")
        self.tabs.addTab(page_librarians, "Библиотекари")
        self.tabs.addTab(page_rooms, "Залы")
        page_report = ReportPage()
        self.tabs.addTab(page_report, "Отчет")


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")
        self.setGeometry(0, 0, 1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

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

        self.entrance_label = QLabel("ВХОД", self.centralwidget)
        self.entrance_label.setGeometry(670, 100, 221, 101)
        self.entrance_label.setFont(QFont("AG_CenturyOldStyle", 48))
        self.entrance_label.setStyleSheet("color: rgb(27, 71, 93);")

        self.image_label = QLabel(self.centralwidget)
        self.image_label.setGeometry(60, 120, 411, 421)
        self.image_label.setPixmap(QPixmap("login.png"))
        self.image_label.setScaledContents(True)

        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.admin_window = AdminWindow()

    def try_login(self):
        login = self.login_edit.toPlainText().strip()
        password = self.password_edit.toPlainText().strip()
        if login == "admin" and password == "123456":
            self.admin_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
