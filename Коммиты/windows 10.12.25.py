from PyQt6.QtWidgets import (QMainWindow, QPushButton,
                             QWidget, QLabel, QTextEdit, QTabWidget, QStatusBar, QMessageBox)
from PyQt6.QtGui import QFont, QPixmap
from pages import PageTemplate
from repository import fetch_all, insert_row, update_row, delete_row
from dialogs import RecordDialog

class ReportPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        # Заголовок
        self.title_label = QLabel("Отчет", self)
        self.title_label.setGeometry(0, 48, 200, 40)
        self.title_label.setFont(QFont("AG_CenturyOldStyle", 18))
        self.title_label.setStyleSheet("color: rgb(27, 71, 93);")

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

        # Кнопка Вывести
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
        self.setFixedSize(1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        central = QWidget(self)
        self.setCentralWidget(central)

        label_role = QLabel("Администратор", self)
        label_role.setFont(QFont("AG_CenturyOldStyle", 18))
        label_role.setStyleSheet("color: rgb(27, 71, 93);")
        label_role.setGeometry(1020, 658, 200, 40)

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
            primary_key="id_книги",
            count_title="Количество книг:",
            count_title_pos = (950, 250),
            count_value_pos = (1030, 285),
            search_columns = ["Название", "ISBN"]
        )

        page_readers = PageTemplate(
            title="Читатели",
            columns=readers_cols,
            data=readers,
            table_name="readers",
            primary_key="id_читателя",
            count_title="Количество читателей:",
            count_title_pos=(930, 210),
            count_value_pos=(1035, 245),
            search_columns=["Фамилия", "Имя"]
        )

        page_librarians = PageTemplate(
            title="Библиотекари",
            columns=librarians_cols,
            data=librarians,
            table_name="librarians",
            primary_key="id_библиотекаря",
            search_columns=["Фамилия", "Имя"]
        )

        page_rooms = PageTemplate(
            title="Залы",
            columns=hall_cols,
            data=hall,
            table_name="hall",
            primary_key="id_зала",
            search_columns = ["Название"]
        )

        self.tabs.addTab(page_books, "Книги")
        self.tabs.addTab(page_readers, "Читатели")
        self.tabs.addTab(page_librarians, "Библиотекари")
        self.tabs.addTab(page_rooms, "Залы")
        page_report = ReportPage()
        self.tabs.addTab(page_report, "Отчет")

class LibrarianWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Панель библиотекаря")
        self.setFixedSize(1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        central = QWidget(self)
        self.setCentralWidget(central)

        label_role = QLabel("Библиотекарь", self)
        label_role.setFont(QFont("AG_CenturyOldStyle", 18))
        label_role.setStyleSheet("color: rgb(27, 71, 93);")
        label_role.setGeometry(1030, 658, 200, 40)

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
            }
        """)

        readers, readers_cols = fetch_all("readers")
        issues, issues_cols = fetch_all("issues")
        returns, returns_cols = fetch_all("returns")

        self.issues_page = PageTemplate(
            title="Выдачи",
            columns=issues_cols,
            data=issues,
            table_name="issues",
            primary_key="id_выдачи",
            count_title="Количество выдач:",
            count_title_pos=(940, 250),
            count_value_pos=(1030, 285),
            search_columns=["Фамилия", "Название", "ISBN"],
            hidden_fields=["КоличествоПродлений"]
        )

        self.returns_page = PageTemplate(
            title="Сдачи",
            columns=returns_cols,
            data=returns,
            table_name="returns",
            primary_key="id_сдачи",
            count_title="Количество сдач:",
            count_title_pos=(950, 210),
            count_value_pos=(1030, 245),
            search_columns=["Фамилия", "Название", "ISBN"]
        )

        # Главная
        self.home_page = HomePage(
            issues_page=self.issues_page,
            returns_page=self.returns_page,
            issues_cols=issues_cols,
            returns_cols=returns_cols
        )

        self.tabs.addTab(self.home_page, "Главная")

        self.tabs.addTab(
            PageTemplate(
                title="Читатели",
                columns=readers_cols,
                data=readers,
                table_name="readers",
                primary_key="id_читателя",
                count_title="Количество читателей:",
                count_title_pos=(920, 210),
                count_value_pos=(1030, 245),
                search_columns=["Фамилия", "Имя"]
            ),
            "Читатели"
        )

        self.tabs.addTab(self.issues_page, "Выдачи")
        self.tabs.addTab(self.returns_page, "Сдачи")
        self.tabs.addTab(ReportPage(), "Отчет")

class HomePage(QWidget):
    def __init__(self, issues_page, returns_page, issues_cols, returns_cols):
        super().__init__()

        self.issues_page = issues_page
        self.returns_page = returns_page
        self.issues_cols = issues_cols
        self.returns_cols = returns_cols

        self.lbl_books_title = QLabel("Количество книг:", self)
        self.lbl_books_title.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_books_title.setGeometry(105, 150, 300, 30)
        self.lbl_books_title.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_books_value = QLabel("0", self)
        self.lbl_books_value.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_books_value.setGeometry(200, 220, 100, 30)
        self.lbl_books_value.setStyleSheet("color: rgb(27, 71, 93);")

        # Количество читателей
        self.lbl_readers_title = QLabel("Количество читателей:", self)
        self.lbl_readers_title.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_readers_title.setGeometry(440, 150, 320, 30)
        self.lbl_readers_title.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_readers_value = QLabel("0", self)
        self.lbl_readers_value.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_readers_value.setGeometry(585, 220, 100, 30)
        self.lbl_readers_value.setStyleSheet("color: rgb(27, 71, 93);")

        # Невозвращенные книги
        self.lbl_issues_title = QLabel(
            "Число книг, не возвращенных\n        в библиотеку:",
            self
        )
        self.lbl_issues_title.setFont(QFont("AG_CenturyOldStyle", 19))
        self.lbl_issues_title.setGeometry(800, 110, 450, 120)
        self.lbl_issues_title.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_issues_value = QLabel("0", self)
        self.lbl_issues_value.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_issues_value.setGeometry(980, 220, 100, 30)
        self.lbl_issues_value.setStyleSheet("color: rgb(27, 71, 93);")

        # Кнопки
        self.btn_issue = QPushButton("Выдача", self)
        self.btn_issue.setGeometry(120, 360, 190, 70)
        self.btn_issue.setFont(QFont("AG_CenturyOldStyle", 22))

        self.btn_return = QPushButton("Сдача", self)
        self.btn_return.setGeometry(890, 360, 190, 70)
        self.btn_return.setFont(QFont("AG_CenturyOldStyle", 22))

        self.btn_extend = QPushButton("Продлить", self)
        self.btn_extend.setGeometry(505, 360, 190, 70)
        self.btn_extend.setFont(QFont("AG_CenturyOldStyle", 22))

        for btn in (self.btn_issue, self.btn_return, self.btn_extend):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(179, 195, 208);
                    border: none;
                    color: rgb(27, 71, 93);
                    border-radius: 10px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: rgb(200, 210, 220);
                }
            """)

        self.btn_issue.clicked.connect(self.add_issue)
        self.btn_return.clicked.connect(self.add_return)

        self.update_stats()

    def add_issue(self):
        dialog = RecordDialog(
            columns=self.issues_cols,
            hidden_fields=["КоличествоПродлений"]
        )
        if dialog.exec():
            values = dialog.get_values()
            values["КоличествоПродлений"] = 0
            insert_row("issues", values)
            self.issues_page.refresh_table()
            self.update_stats()

    def add_return(self):
        dialog = RecordDialog(self.returns_cols)
        if dialog.exec():
            insert_row("returns", dialog.get_values())
            self.returns_page.refresh_table()
            self.update_stats()

    def update_stats(self):
        books, _ = fetch_all("books")
        readers, _ = fetch_all("readers")
        issues, _ = fetch_all("issues")

        self.lbl_books_value.setText(str(len(books)))
        self.lbl_readers_value.setText(str(len(readers)))
        self.lbl_issues_value.setText(str(len(issues)))

    def update_stats(self):
        books, _ = fetch_all("books")
        readers, _ = fetch_all("readers")
        issues, _ = fetch_all("issues")

        self.lbl_books_value.setText(str(len(books)))
        self.lbl_readers_value.setText(str(len(readers)))
        self.lbl_issues_value.setText(str(len(issues)))

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")
        self.setFixedSize(1200, 700)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

        self.login_error = QLabel("Заполните логин", self.centralwidget)
        self.login_error.setGeometry(810, 295, 321, 20)
        self.login_error.setStyleSheet("color: red;")
        self.login_error.hide()

        self.password_error = QLabel("Заполните пароль", self.centralwidget)
        self.password_error.setGeometry(810, 385, 321, 20)
        self.password_error.setStyleSheet("color: red;")
        self.password_error.hide()

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

        has_error = False

        if not login:
            self.login_error.show()
            has_error = True
        else:
            self.login_error.hide()
            self.login_edit.setStyleSheet("""
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
            """)

        # Проверка пароля
        if not password:
            self.password_error.show()
            has_error = True
        else:
            self.password_error.hide()
            self.password_edit.setStyleSheet("""
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
            """)

        if has_error:
            return

        if login == "admin" and password == "123456":
            self.admin = AdminWindow()
            self.admin.show()
            self.close()

        elif login == "library" and password == "654321":
            self.librarian = LibrarianWindow()
            self.librarian.show()
            self.close()

        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")