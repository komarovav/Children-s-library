from PyQt6.QtWidgets import (QMainWindow, QPushButton,
                             QWidget, QLabel, QTextEdit, QTabWidget, QStatusBar, QDialog, QMessageBox)
from PyQt6.QtGui import QFont, QPixmap
from pages import PageTemplate, RenewalDialog
from repository import fetch_all, insert_row
from dialogs import RecordDialog
from db import get_connection

TECH_TO_HUMAN = {
    "ГодИздания": "Год издания",
    "ВозрастноеОграничение": "Возрастное ограничение",
    "ДатаВыдачи": "Дата выдачи",
    "ДатаВозврата": "Дата возврата",
    "ДатаРождения": "Дата рождения",
    "КонтактРодителя": "Контакт родителя",
    "ДатаСдачи": "Дата сдачи",
}

HUMAN_TO_TECH = {v: k for k, v in TECH_TO_HUMAN.items()}

class ReportPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.title_label = QLabel("Отчет", self)
        self.title_label.setGeometry(0, 48, 200, 40)
        self.title_label.setFont(QFont("AG_CenturyOldStyle", 18))
        self.title_label.setStyleSheet("color: rgb(27, 71, 93);")

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
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    r.Фамилия,
                    r.Имя,
                    r.Отчество,
                    r.КонтактРодителя AS Телефон,
                    b.Название AS Книга,
                    i.ДатаВозврата
                FROM issues i
                JOIN readers r ON i.id_читателя = r.id_читателя
                JOIN books b ON i.id_книги = b.id_книги
                WHERE 
                    i.ДатаВозврата < CURDATE()  -- просрочено
                    AND i.id_выдачи NOT IN (SELECT id_выдачи FROM returns)  -- не сдано
                ORDER BY i.ДатаВозврата
            """)
            rows = cur.fetchall()
            conn.close()

            if not rows:
                self.report_output.setText("Нет читателей, не вернувших книги в срок.")
                return

            report_lines = ["Список читателей, не вернувших книги в срок:\n"]
            for i, row in enumerate(rows, 1):
                fio = f"{row['Фамилия']} {row['Имя']} {row.get('Отчество', '')}".strip()
                phone = row.get('Телефон') or "Не указан"
                book = row.get('Книга') or "Неизвестна"
                due_date = row['ДатаВозврата'].strftime("%d.%m.%Y") if row['ДатаВозврата'] else "Не указана"

                report_lines.append(f"{i}. {fio}")
                report_lines.append(f"   Телефон: {phone}")
                report_lines.append(f"   Книга: {book}")
                report_lines.append(f"   Срок возврата: {due_date}\n")

            self.report_output.setText("\n".join(report_lines))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сформировать отчёт:\n{str(e)}")
            self.report_output.setText("Ошибка при загрузке данных.")

class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Окно администратора")
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

        display_books = {
            "id_книги": "ID",
            "Название": "Название",
            "Жанр": "Жанр",
            "ГодИздания": "Год издания",
            "ВозрастноеОграничение": "Возраст. ограничение",
            "ISBN": "ISBN",
            "ББК": "ББК",
            "Количество": "Количество",
            "id_зала": "Зал"
        }

        books, books_cols = fetch_all("books")
        self.page_books = PageTemplate(
            title="Книги",
            columns=books_cols,
            display_names=display_books,
            data=books,
            table_name="books",
            primary_key="id_книги",
            count_title="Количество книг:",
            count_title_pos=(950, 250),
            count_value_pos=(1030, 285),
            count_sum_field="Количество",
            hidden_fields=["id_книги"]
        )

        self.page_readers = None
        self.page_librarians = None
        self.page_rooms = None
        self.page_report = ReportPage()

        self.tabs.addTab(self.page_books, "Книги")
        self.tabs.addTab(QWidget(), "Читатели")
        self.tabs.addTab(QWidget(), "Библиотекари")
        self.tabs.addTab(QWidget(), "Залы")
        self.tabs.addTab(self.page_report, "Отчет")

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        display_readers = {
            "id_читателя": "ID",
            "Фамилия": "Фамилия",
            "Имя": "Имя",
            "Отчество": "Отчество",
            "ДатаРождения": "Дата рождения",
            "КонтактРодителя": "Контакт родителя",
            "Комментарий": "Комментарий"
        }
        display_librarians = {
            "id_библиотекаря": "ID",
            "Логин": "Логин",
            "Пароль": "Пароль",
            "Фамилия": "Фамилия",
            "Имя": "Имя",
            "Отчество": "Отчество",
            "id_зала": "Зал"
        }
        display_rooms = {
            "id_зала": "ID",
            "Название": "Название",
            "Этаж": "Этаж"
        }

        if index == 1 and self.page_readers is None:
            readers, readers_cols = fetch_all("readers")
            self.page_readers = PageTemplate(
                title="Читатели",
                columns=readers_cols,
                display_names=display_readers,
                data=readers,
                table_name="readers",
                primary_key="id_читателя",
                count_title="Количество читателей:",
                count_title_pos=(930, 210),
                count_value_pos=(1035, 245),
                search_columns=["Фамилия", "Имя"],
                hidden_fields=["id_читателя"]
            )
            self.tabs.removeTab(1)
            self.tabs.insertTab(1, self.page_readers, "Читатели")
            self.tabs.setCurrentIndex(1)

        elif index == 2 and self.page_librarians is None:
            librarians, librarians_cols = fetch_all("librarians")
            librarians = [lib for lib in librarians if lib.get("Логин") != "admin"]
            self.page_librarians = PageTemplate(
                title="Библиотекари",
                columns=librarians_cols,
                display_names=display_librarians,
                data=librarians,
                table_name="librarians",
                primary_key="id_библиотекаря",
                search_columns=["Фамилия", "Имя"],
                hidden_fields=["id_библиотекаря"]
            )
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.page_librarians, "Библиотекари")
            self.tabs.setCurrentIndex(2)

        elif index == 3 and self.page_rooms is None:
            hall, hall_cols = fetch_all("hall")
            self.page_rooms = PageTemplate(
                title="Залы",
                columns=hall_cols,
                display_names=display_rooms,
                data=hall,
                table_name="hall",
                primary_key="id_зала",
                search_columns=["Название"],
                hidden_fields=["id_зала", "Зал"]
            )
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.page_rooms, "Залы")
            self.tabs.setCurrentIndex(3)

class LibrarianWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Окно библиотекаря")
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

        self.home_page = HomePage()
        self.tabs.addTab(self.home_page, "Главная")

        self.page_readers = None
        self.page_issues = None
        self.page_returns = None
        self.page_report = None

        self.tabs.addTab(QWidget(), "Читатели")
        self.tabs.addTab(QWidget(), "Выдачи")
        self.tabs.addTab(QWidget(), "Сдачи")
        self.tabs.addTab(QWidget(), "Отчет")

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def update_overdue_stats(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) AS overdue_count
                FROM issues i
                WHERE 
                    i.ДатаВозврата < CURDATE()
                    AND i.id_выдачи NOT IN (SELECT id_выдачи FROM returns)
            """)
            overdue_count = cur.fetchone()["overdue_count"]
            conn.close()
            return str(overdue_count)
        except Exception as e:
            return "–"
    def on_tab_changed(self, index):
        display_readers = {
            "id_читателя": "ID",
            "Фамилия": "Фамилия",
            "Имя": "Имя",
            "Отчество": "Отчество",
            "ДатаРождения": "Дата рождения",
            "КонтактРодителя": "Контакт родителя",
            "Комментарий": "Комментарий"
        }
        if index == 1 and self.page_readers is None:
            _, readers_cols = fetch_all("readers")
            readers, _ = fetch_all("readers")
            self.page_readers = PageTemplate(
                title="Читатели",
                columns=readers_cols,
                display_names=display_readers,
                data=readers,
                table_name="readers",
                primary_key="id_читателя",
                count_title="Количество читателей:",
                count_title_pos=(920, 210),
                count_value_pos=(1030, 245),
                search_columns=["Фамилия", "Имя"],
                hidden_fields=["id_читателя"],
            )
            self.tabs.removeTab(1)
            self.tabs.insertTab(1, self.page_readers, "Читатели")
            self.tabs.setCurrentIndex(1)

        elif index == 2 and self.page_issues is None:
            display_issues = {
                "id_выдачи": "ID",
                "id_читателя": "Читатель",
                "id_книги": "Книга",
                "id_библиотекаря": "Библиотекарь",
                "ДатаВыдачи": "Дата выдачи",
                "ДатаВозврата": "Дата возврата",
                "КоличествоПродлений": "Количество продлений"
            }
            _, issues_cols = fetch_all("issues")
            issues, _ = fetch_all("issues")
            self.page_issues = PageTemplate(
                title="Выдачи",
                columns=issues_cols,
                display_names=display_issues,
                data=issues,
                table_name="issues",
                primary_key="id_выдачи",
                count_title_pos=(940, 250),
                count_value_pos=(1030, 285),
                hidden_fields=["КоличествоПродлений", "id_выдачи"],
                show_overdue_stats=True,
                stats_updater=self.update_overdue_stats
            )
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.page_issues, "Выдачи")
            self.tabs.setCurrentIndex(2)

        elif index == 3 and self.page_returns is None:
            display_returns = {
                "id_сдачи": "ID",
                "id_выдачи": "Выдача",
                "ДатаСдачи": "Дата сдачи",
                "Комментарий": "Комментарий"
            }
            _, returns_cols = fetch_all("returns")
            returns, _ = fetch_all("returns")
            self.page_returns = PageTemplate(
                title="Сдачи",
                columns=returns_cols,
                display_names=display_returns,
                data=returns,
                table_name="returns",
                primary_key="id_сдачи",
                count_title_pos=(950, 210),
                count_value_pos=(1030, 245),
                hidden_fields=["id_сдачи"],
                show_overdue_stats=True,
                stats_updater=self.update_overdue_stats
            )
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.page_returns, "Сдачи")
            self.tabs.setCurrentIndex(3)

        elif index == 4 and self.page_report is None:
            self.page_report = ReportPage()
            self.tabs.removeTab(4)
            self.tabs.insertTab(4, self.page_report, "Отчет")
            self.tabs.setCurrentIndex(4)

    def refresh_all_pages(self):
        if self.page_issues is not None:
            self.page_issues.refresh_table()
        if self.page_returns is not None:
            self.page_returns.refresh_table()
        if self.page_readers is not None:
            self.page_readers.refresh_table()

class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        self.lbl_books_title = QLabel("Количество книг:", self)
        self.lbl_books_title.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_books_title.setGeometry(105, 150, 300, 30)
        self.lbl_books_title.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_books_value = QLabel("0", self)
        self.lbl_books_value.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_books_value.setGeometry(200, 220, 100, 30)
        self.lbl_books_value.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_readers_title = QLabel("Количество читателей:", self)
        self.lbl_readers_title.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_readers_title.setGeometry(440, 150, 320, 30)
        self.lbl_readers_title.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_readers_value = QLabel("0", self)
        self.lbl_readers_value.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_readers_value.setGeometry(585, 220, 100, 30)
        self.lbl_readers_value.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_issues_title = QLabel(
            "Число книг, не возвращенных\n    в библиотеку (в срок):",
            self
        )
        self.lbl_issues_title.setFont(QFont("AG_CenturyOldStyle", 19))
        self.lbl_issues_title.setGeometry(800, 110, 450, 120)
        self.lbl_issues_title.setStyleSheet("color: rgb(27, 71, 93);")

        self.lbl_issues_value = QLabel("0", self)
        self.lbl_issues_value.setFont(QFont("AG_CenturyOldStyle", 20))
        self.lbl_issues_value.setGeometry(980, 220, 100, 30)
        self.lbl_issues_value.setStyleSheet("color: rgb(27, 71, 93);")

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
        self.update_stats_safe()
        self.btn_issue.clicked.connect(self.add_issue)
        self.btn_return.clicked.connect(self.add_return)
        self.btn_extend.clicked.connect(self.add_renewal)

    def add_renewal(self):
        dialog = RenewalDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_renewal_data()
            issue_id = data['issue_id']
            new_date = data['new_return_date']

            if not issue_id:
                QMessageBox.warning(self, "Ошибка", "Выберите выдачу для продления")
                return

            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) AS cnt FROM returns WHERE id_выдачи = %s", (issue_id,))
                is_returned = cur.fetchone()["cnt"] > 0
                conn.close()

                if is_returned:
                    QMessageBox.warning(self, "Ошибка", "Нельзя продлить выдачу, которая уже сдана!")
                    return

                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE issues 
                    SET ДатаВозврата = %s,
                        КоличествоПродлений = COALESCE(КоличествоПродлений, 0) + 1
                    WHERE id_выдачи = %s
                """, (new_date, issue_id))
                conn.commit()
                conn.close()

                self.window().refresh_all_pages()
                self.update_stats_safe()
                QMessageBox.information(self, "Успех", "Выдача успешно продлена!")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось продлить выдачу: {e}")

    def add_issue(self):
        def save_callback(values):
            tech_values = {}
            for key, value in values.items():
                tech_key = HUMAN_TO_TECH.get(key, key)
                tech_values[tech_key] = value
            values = tech_values
            reader_id = values.pop("Читатель", None)
            book_id = values.pop("Книга", None)
            librarian_id = values.pop("Библиотекарь", None)

            if reader_id is None:
                QMessageBox.warning(self, "Ошибка", "Выберите читателя")
                return
            if book_id is None:
                QMessageBox.warning(self, "Ошибка", "Выберите книгу")
                return
            if librarian_id is None:
                QMessageBox.warning(self, "Ошибка", "Выберите библиотекаря")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT Количество FROM books WHERE id_книги = %s", (book_id,))
            row = cur.fetchone()
            if not row or row["Количество"] <= 0:
                QMessageBox.warning(self, "Ошибка", "Эта книга недоступна для выдачи")
                conn.close()
                return
            conn.close()

            values["id_читателя"] = reader_id
            values["id_книги"] = book_id
            values["id_библиотекаря"] = librarian_id

            insert_row("issues", values)

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE books SET Количество = Количество - 1 WHERE id_книги = %s", (book_id,))
            conn.commit()
            conn.close()

            self.window().refresh_all_pages()
            self.update_stats_safe()

        _, raw_cols = fetch_all("issues")
        columns_with_fk = raw_cols.copy()

        if "id_читателя" in columns_with_fk:
            columns_with_fk[columns_with_fk.index("id_читателя")] = "Читатель"
        if "id_книги" in columns_with_fk:
            columns_with_fk[columns_with_fk.index("id_книги")] = "Книга"
        if "id_библиотекаря" in columns_with_fk:
            columns_with_fk[columns_with_fk.index("id_библиотекаря")] = "Библиотекарь"

        if "ДатаВыдачи" in columns_with_fk:
            columns_with_fk[columns_with_fk.index("ДатаВыдачи")] = "Дата выдачи"
        if "ДатаВозврата" in columns_with_fk:
            columns_with_fk[columns_with_fk.index("ДатаВозврата")] = "Дата возврата"

        for col in ["Читатель", "Книга", "Библиотекарь"]:
            if col not in columns_with_fk:
                columns_with_fk.append(col)

        dialog = RecordDialog(
            columns=columns_with_fk,
            save_callback=save_callback,
            hidden_fields=["КоличествоПродлений", "id_выдачи"],
            close_on_save=True,
            table_name="issues"
        )
        self.update_stats()
        dialog.exec()

    def add_return(self):
        def save_callback(values):
            tech_values = {}
            for key, value in values.items():
                tech_key = HUMAN_TO_TECH.get(key, key)
                tech_values[tech_key] = value
            values = tech_values
            issue_id = values.pop("Выдача", None)
            if not issue_id:
                QMessageBox.warning(self, "Ошибка", "Выберите выдачу")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id_книги FROM issues WHERE id_выдачи = %s", (issue_id,))
            issue_row = cur.fetchone()

            if not issue_row:
                QMessageBox.warning(self, "Ошибка", "Выдача не найдена")
                conn.close()
                return

            book_id = issue_row["id_книги"]
            conn.close()

            values["id_выдачи"] = issue_id
            insert_row("returns", values)

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE books SET Количество = Количество + 1 WHERE id_книги = %s", (book_id,))
            conn.commit()
            conn.close()

            self.window().refresh_all_pages()
            self.update_stats_safe()

        _, raw_cols = fetch_all("returns")
        columns_with_fk = raw_cols.copy()
        if "id_выдачи" in columns_with_fk:
            columns_with_fk[columns_with_fk.index("id_выдачи")] = "Выдача"

        if "ДатаСдачи" in columns_with_fk:
            columns_with_fk[columns_with_fk.index("ДатаСдачи")] = "Дата сдачи"

        dialog = RecordDialog(
            columns=columns_with_fk,
            save_callback=save_callback,
            hidden_fields=["id_сдачи"],
            close_on_save=True,
            table_name="returns"
        )
        self.update_stats()
        dialog.exec()
    def update_stats_safe(self):
        try:
            self.update_stats()
        except Exception as e:
            self.lbl_books_value.setText("–")
            self.lbl_readers_value.setText("–")
            self.lbl_issues_value.setText("–")

    def update_stats(self):
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("SELECT COALESCE(SUM(Количество), 0) AS total_books FROM books")
            total_books = cur.fetchone()["total_books"]
            self.lbl_books_value.setText(str(int(total_books)))

            cur.execute("SELECT COUNT(*) AS total_readers FROM readers")
            total_readers = cur.fetchone()["total_readers"]
            self.lbl_readers_value.setText(str(total_readers))

            cur.execute("""
                SELECT COUNT(*) AS overdue_count
                FROM issues i
                WHERE 
                    i.ДатаВозврата < CURDATE()
                    AND i.id_выдачи NOT IN (SELECT id_выдачи FROM returns)
            """)
            overdue_count = cur.fetchone()["overdue_count"]
            self.lbl_issues_value.setText(str(overdue_count))
            if hasattr(self, 'page_issues') and self.page_issues:
                self.page_issues.refresh_overdue_stats()
            if hasattr(self, 'page_returns') and self.page_returns:
                self.page_returns.refresh_overdue_stats()
            conn.close()

        except Exception as e:
            self.lbl_books_value.setText("–")
            self.lbl_readers_value.setText("–")
            self.lbl_issues_value.setText("–")

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Окно регистрации")
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
        self.image_label.setPixmap(QPixmap("Images/login.png"))
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

        if not password:
            self.password_error.show()
            has_error = True
        else:
            self.password_error.hide()

        if has_error:
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT Логин, Пароль 
                FROM librarians 
                WHERE Логин = %s
            """, (login,))
            user = cur.fetchone()
            conn.close()

            if user and user["Пароль"] == password:
                if login == "admin":
                    self.admin = AdminWindow()
                    self.admin.show()
                    self.close()
                else:
                    self.librarian = LibrarianWindow()
                    self.librarian.show()
                    self.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных:\n{str(e)}")