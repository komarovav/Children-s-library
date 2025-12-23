from PyQt6.QtWidgets import (QWidget, QDialog, QHeaderView, QHBoxLayout, QVBoxLayout,
                             QTableWidget, QLabel, QTableWidgetItem, QPushButton,
                             QLineEdit, QMessageBox, QStyledItemDelegate)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize, Qt
from dialogs import RecordDialog, ConfirmDeleteDialog, RenewalDialog
from repository import fetch_all, insert_row, update_row, delete_row, get_next_author_id
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

TABLE_TO_HUMAN = {
    "ГодИздания": "Год издания",
    "ВозрастноеОграничение": "Возраст. ограничение",
    "ДатаВыдачи": "Дата выдачи",
    "ДатаВозврата": "Дата возврата",
    "ДатаРождения": "Дата рождения",
    "КонтактРодителя": "Контакт родителя",
    "ДатаСдачи": "Дата сдачи",
    "id_книги": "Книга",
    "id_читателя": "Чиатель",
    "id_библиотекаря": "Библиотекарь",
    "id_зала": "Зал",
    "id_выдачи": "Выдача",
    "id_сдачи": "ID"
}

HUMAN_TO_TABLE = {v: k for k, v in TABLE_TO_HUMAN.items()}
class Field(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setFrame(False)
        editor.setStyleSheet(
            "background-color: white; color: rgb(27, 71, 93); padding: 5px;"
        )
        editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        return editor

    def setEditorData(self, editor, index):
        editor.setText(index.data() or "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class AuthorsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_name = "authors"
        self.primary_key = "id_автора"

        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setItemDelegate(Field(self.table))
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: white; 
                color: rgb(27, 71, 93);
                border: 2px solid rgb(179, 195, 208); 
                border-radius: 5px; 
                gridline-color: rgb(179, 195, 208);
            }
            QHeaderView::section { 
                background-color: rgb(179, 195, 208);
                color: rgb(27, 71, 93); 
                padding: 5px; 
                font-size: 18px; 
            }
            QTableWidget::item { padding: 10px; font-size: 16px; }
            QScrollBar:horizontal {
                border: 1px solid rgb(179, 195, 208);
                background: rgb(240, 240, 240);
                height: 15px;
                margin: 0px 20px 0 20px;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                width: 12px;
                background: rgb(240, 240, 240);
                border: 1px solid rgb(179, 195, 208);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #a0a0a0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #808080;
            }

            /* Убираем стрелки */
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
            }
        """)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.CurrentChanged |
            QTableWidget.EditTrigger.DoubleClicked
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        default_columns = ["id_автора", "Фамилия", "Имя", "Отчество"]
        self.table.setColumnCount(len(default_columns))
        self.table.setHorizontalHeaderLabels(default_columns)

        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        header.setSectionsMovable(False)

        self.layout.addWidget(self.table)

        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 10px;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: rgb(200, 210, 220); }
        """)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 10px;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: rgb(200, 210, 220); }
        """)


        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.delete_btn)
        self.layout.addLayout(buttons_layout)

        self.delete_btn.clicked.connect(self.delete_author_row)
        self.save_btn.clicked.connect(self.save_authors)

        self.load_authors()
        self.add_empty_row()

    def load_authors(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {self.table_name} ORDER BY Фамилия, Имя")
            rows = cur.fetchall()
            conn.close()

            if not rows:
                self.table.setColumnCount(4)
                self.table.setHorizontalHeaderLabels(["id_автора", "Фамилия", "Имя", "Отчество"])
                self.table.setRowCount(0)
                return

            columns = list(rows[0].keys())
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(0)

            for row_data in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col_index, col_name in enumerate(columns):
                    item = QTableWidgetItem(str(row_data[col_name]) if row_data[col_name] is not None else "")
                    if col_index == 0:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, col_index, item)

            self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки авторов", str(e))

    def add_empty_row(self):
        self.table.setSortingEnabled(False)
        row = self.table.rowCount()
        self.table.insertRow(row)

        next_id = get_next_author_id()

        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            if col == 0:  # id_автора
                item.setText(str(next_id))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, col, item)

        self.table.selectRow(row)

    def delete_author_row(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        id_item = self.table.item(row, 0)
        if id_item and id_item.text():
            try:
                delete_row(self.table_name, id_item.text(), self.primary_key)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка удаления", str(e))
        self.table.removeRow(row)

    def save_authors(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            for row in range(self.table.rowCount()):
                row_data = {}
                empty_row = True
                for col in range(self.table.columnCount()):
                    header = self.table.horizontalHeaderItem(col).text()
                    item = self.table.item(row, col)
                    value = item.text().strip() if item else None
                    if value:
                        empty_row = False
                    row_data[header] = value

                if empty_row:
                    continue

                required_fields = ["Фамилия", "Имя"]
                missing_fields = [f for f in required_fields if not row_data[f]]
                if missing_fields:
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        f"Поля обязательны для заполнения: {', '.join(missing_fields)}"
                    )
                    continue

                pk_value = row_data["id_автора"]

                cur.execute("SELECT COUNT(*) AS cnt FROM authors WHERE id_автора=%s", (pk_value,))
                exists = cur.fetchone()["cnt"] > 0

                if exists:
                    cur.execute(
                        "UPDATE authors SET Фамилия=%s, Имя=%s, Отчество=%s WHERE id_автора=%s",
                        (row_data["Фамилия"], row_data["Имя"], row_data["Отчество"], pk_value)
                    )
                else:
                    cur.execute(
                        "INSERT INTO authors (Фамилия, Имя, Отчество) VALUES (%s, %s, %s)",
                        (row_data["Фамилия"], row_data["Имя"], row_data["Отчество"])
                    )
                    row_data["id_автора"] = cur.lastrowid
            conn.commit()
            conn.close()

            self.load_authors()
            self.add_empty_row()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения авторов", str(e))

class PageTemplate(QWidget):
    def __init__(self, title: str, columns: list[str], data: list[dict], table_name: str,
                 primary_key: str = "id", count_title: str | None = None,
                 count_title_pos: tuple[int, int] | None = None, count_value_pos: tuple[int, int] | None = None,
                 count_sum_field: str | None = None, search_columns: list[str] | None = None, hidden_fields=None, display_names: dict = None, show_overdue_stats=False,
                 stats_updater=None ):
        super().__init__()
        self.table_name = table_name
        self.primary_key = primary_key
        self.columns = columns
        self.count_sum_field = count_sum_field
        self.search_columns = search_columns or []
        self.hidden_fields = hidden_fields or []
        self.display_names = display_names or {}
        self.show_overdue_stats = show_overdue_stats
        self.stats_updater = stats_updater
        SEARCH_HINTS = {
            "readers": "по фамилии и имени",
            "books": "по названию, ISBN и автору",
            "librarians": "по фамилии и имени",
            "issues": "по фамилии читателя, названию книги или ISBN",
            "returns": "по фамилии читателя, названию книги или ISBN",
            "hall": "по названию"
        }
        self.search_input = QLineEdit(self)
        self.search_input.textChanged.connect(self.on_search)
        self.search_input.setPlaceholderText(f"Поиск {SEARCH_HINTS.get(self.table_name, '...')}")
        self.search_input.setFont(QFont("AG_CenturyOldStyle", 16))
        self.search_input.setGeometry(270, 25, 600, 50)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                padding: 10px;
                border-radius: 15px;
                color: rgb(27, 71, 93);
            }
            QLineEdit::placeholder { color: rgb(27, 71, 93); }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 80, 0, 0)

        label = QLabel(title, self)
        label.setFont(QFont("AG_CenturyOldStyle", 18))
        label.setStyleSheet("color: rgb(27, 71, 93);")
        label.setGeometry(0, 48, 200, 40)

        self.table = QTableWidget(self)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(35)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setGeometry(0, 80, 870, 550)

        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        headers = []
        for col in self.columns:
            # Специальная обработка для id-полей в зависимости от таблицы
            if col == "id_читателя":
                if self.table_name == "readers":
                    headers.append("ID")
                else:
                    headers.append("Читатель")
            elif col == "id_книги":
                if self.table_name == "books":
                    headers.append("ID")
                else:
                    headers.append("Книга")
            elif col == "id_библиотекаря":
                if self.table_name == "librarians":
                    headers.append("ID")
                else:
                    headers.append("Библиотекарь")
            elif col == "id_зала":
                if self.table_name == "hall":
                    headers.append("ID")
                else:
                    headers.append("Зал")
            elif col == "id_выдачи":
                if self.table_name == "issues":
                    headers.append("ID")
                else:
                    headers.append("Выдача")
            elif col == "id_сдачи":
                headers.append("ID")  # Только в таблице returns
            else:
                # Обработка обычных полей (даты, возраст и т.д.)
                headers.append(TABLE_TO_HUMAN.get(col, col))
        self.table.setHorizontalHeaderLabels(headers)

        header = self.table.horizontalHeader()
        if len(columns) <= 5:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        else:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            for i in range(len(columns)):
                self.table.setColumnWidth(i, 200)
        self.table.setColumnWidth(0, 60)
        header.setStretchLastSection(False)
        header.setSectionsMovable(False)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: rgb(27, 71, 93);
                border: 2px solid rgb(179, 195, 208);
                border-radius: 5px;
                gridline-color: rgb(179, 195, 208);
                /* Убираем внутренние отступы */
                padding: 0px;
            }
            QHeaderView::section {
                background-color: rgb(179, 195, 208);
                color: rgb(27, 71, 93);
                padding: 5px;
                font-size: 18px;
                border: none;
            }
            QHeaderView::section:selected {
                background-color: rgb(200, 210, 220);  /* цвет при выделении */
                color: rgb(27, 71, 93);
            }
            QTableWidget::item {
                padding: 10px;
            }

            /* Скроллбары без margin */
            QScrollBar:horizontal {
                height: 12px;
                background: rgb(240, 240, 240);
                border: 1px solid rgb(179, 195, 208);
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #a0a0a0;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #808080;
            }

            QScrollBar:vertical {
                width: 12px;
                background: rgb(240, 240, 240);
                border: 1px solid rgb(179, 195, 208);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #a0a0a0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #808080;
            }

            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
            }
        """)
        if self.show_overdue_stats and self.stats_updater:
            self.overdue_title = QLabel(
                "Число книг, не возвращенных\n    в библиотеку (в срок):",
                self
            )
            self.overdue_title.setFont(QFont("AG_CenturyOldStyle", 14))
            self.overdue_title.setGeometry(900, 210, 450, 120)
            self.overdue_title.setStyleSheet("color: rgb(27, 71, 93);")

            self.overdue_value = QLabel("0", self)
            self.overdue_value.setFont(QFont("AG_CenturyOldStyle", 16))
            self.overdue_value.setGeometry(1040, 310, 100, 30)
            self.overdue_value.setStyleSheet("color: rgb(27, 71, 93);")

            self.refresh_overdue_stats()
        else:
            self.overdue_title = None
            self.overdue_value = None

        if count_title:
            x_title, y_title = count_title_pos
            x_value, y_value = count_value_pos
            self.count_label_text = QLabel(count_title, self)
            self.count_label_text.setFont(QFont("AG_CenturyOldStyle", 16))
            self.count_label_text.setGeometry(x_title, y_title, 250, 30)
            self.count_label_text.setStyleSheet("color: rgb(27, 71, 93);")

            self.count_label_value = QLabel("0", self)
            self.count_label_value.setFont(QFont("AG_CenturyOldStyle", 18))
            self.count_label_value.setGeometry(x_value, y_value, 100, 40)
            self.count_label_value.setStyleSheet("color: rgb(27, 71, 93);")
        else:
            self.count_label_text = None
            self.count_label_value = None

        # Кнопки
        btn_add = QPushButton("Добавить", self)
        btn_add.setFont(QFont("AG_CenturyOldStyle", 16))
        btn_add.setGeometry(997, 80, 160, 50)
        btn_add.setStyleSheet("""
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
        # Кнопка +Автор
        if self.table_name == "books":
            btn_author = QPushButton("+Автор", self)
            btn_author.setFont(QFont("AG_CenturyOldStyle", 16))
            btn_author.setGeometry(997, 150, 160, 50)
            btn_author.clicked.connect(self.open_authors)
            btn_author.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 10px;  /* скругление всей кнопки */
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)

        if self.table_name == "issues":
            btn_renew = QPushButton("Продлить", self)
            btn_renew.setFont(QFont("AG_CenturyOldStyle", 16))
            btn_renew.setGeometry(997, 150, 160, 50)
            btn_renew.clicked.connect(self.renew_selected_issue)
            btn_renew.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 10px;  /* скругление всей кнопки */
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)

        btn_edit = QPushButton(self)
        btn_edit.setIcon(QIcon("Images/edit.png"))
        btn_edit.setIconSize(QSize(20, 20))
        btn_edit.setGeometry(867, 80, 48, 45)
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)

        btn_delete = QPushButton(self)
        btn_delete.setIcon(QIcon("Images/delete.png"))
        btn_delete.setIconSize(QSize(20, 20))
        btn_delete.setGeometry(914, 80, 48, 45)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: rgb(179, 195, 208);
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """)

        btn_add.clicked.connect(self.add_record)
        btn_edit.clicked.connect(self.edit_record)
        btn_delete.clicked.connect(self.delete_record)

        self.refresh_table(data)

    def refresh_overdue_stats(self):
        if self.overdue_value and self.stats_updater:
            value = self.stats_updater()
            self.overdue_value.setText(value)

    def renew_selected_issue(self):
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

                if is_returned:
                    QMessageBox.warning(self, "Ошибка", "Нельзя продлить выдачу, которая уже сдана!")
                    conn.close()
                    return

                cur.execute("""
                    UPDATE issues 
                    SET ДатаВозврата = %s,
                        КоличествоПродлений = COALESCE(КоличествоПродлений, 0) + 1
                    WHERE id_выдачи = %s
                """, (new_date, issue_id))
                conn.commit()
                conn.close()

                self.refresh_table()


            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось продлить выдачу: {e}")

    def _search_returns(self, text: str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                r.id_сдачи,
                r.id_выдачи,
                r.ДатаСдачи,
                r.Комментарий
            FROM returns r
            JOIN issues i ON r.id_выдачи = i.id_выдачи
            JOIN readers rd ON i.id_читателя = rd.id_читателя
            JOIN books b ON i.id_книги = b.id_книги
            WHERE 
                rd.Фамилия LIKE %s OR
                b.Название LIKE %s OR
                b.ISBN LIKE %s
        """, (f"%{text}%", f"%{text}%", f"%{text}%"))

        filtered_data = []
        for row in cur.fetchall():
            data_row = {
                "id_сдачи": row["id_сдачи"],
                "id_выдачи": row["id_выдачи"],
                "ДатаСдачи": row["ДатаСдачи"],
                "Комментарий": row["Комментарий"]
            }
            filtered_data.append(data_row)

        conn.close()

        self.refresh_table(filtered_data)

    def _search_books(self, text: str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT
                b.id_книги,
                b.Название,
                b.Жанр,
                b.ГодИздания,
                b.ВозрастноеОграничение,
                b.ISBN,
                b.ББК,
                b.Количество,
                b.id_зала
            FROM books b
            LEFT JOIN book_authors ba ON b.id_книги = ba.id_книги
            LEFT JOIN authors a ON ba.id_автора = a.id_автора
            WHERE 
                b.Название LIKE %s OR
                b.ISBN LIKE %s OR
                a.Фамилия LIKE %s OR
                a.Имя LIKE %s
        """, (f"%{text}%", f"%{text}%", f"%{text}%", f"%{text}%"))

        filtered_data = []
        for row in cur.fetchall():
            data_row = {
                "id_книги": row["id_книги"],
                "Название": row["Название"],
                "Жанр": row["Жанр"],
                "ГодИздания": row["ГодИздания"],
                "ВозрастноеОграничение": row["ВозрастноеОграничение"],
                "ISBN": row["ISBN"],
                "ББК": row["ББК"],
                "Количество": row["Количество"],
                "id_зала": row["id_зала"],
            }
            filtered_data.append(data_row)

        cur.close()
        conn.close()

        self.refresh_table(filtered_data)

    def _search_issues(self, text: str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                i.id_выдачи,
                i.id_читателя,
                i.id_книги,
                i.id_библиотекаря,
                i.ДатаВыдачи,
                i.ДатаВозврата,
                i.КоличествоПродлений
            FROM issues i
            JOIN readers r ON i.id_читателя = r.id_читателя
            JOIN books b ON i.id_книги = b.id_книги
            WHERE 
                r.Фамилия LIKE %s OR
                b.Название LIKE %s OR
                b.ISBN LIKE %s
        """, (f"%{text}%", f"%{text}%", f"%{text}%"))

        filtered_data = []
        for row in cur.fetchall():
            data_row = {
                "id_выдачи": row["id_выдачи"],
                "id_читателя": row["id_читателя"],
                "id_книги": row["id_книги"],
                "id_библиотекаря": row["id_библиотекаря"],
                "ДатаВыдачи": row["ДатаВыдачи"],
                "ДатаВозврата": row["ДатаВозврата"],
                "КоличествоПродлений": row["КоличествоПродлений"]
            }
            filtered_data.append(data_row)

        cur.close()
        conn.close()

        self.refresh_table(filtered_data)
    def on_search(self, text: str):
        text = text.strip().lower()
        if not text:
            self.refresh_table()
            return
        if self.table_name == "returns":
            self._search_returns(text)
            return
        elif self.table_name == "issues":
            self._search_issues(text)
            return
        elif self.table_name == "books":
            self._search_books(text)
            return
        data, _ = fetch_all(self.table_name)
        filtered = []
        for row in data:
            for col in self.search_columns:
                value = str(row.get(col, "")).lower()
                if text in value:
                    filtered.append(row)
                    break

        self.refresh_table(filtered)

    def open_authors(parent):
        try:
            dialog = QDialog(parent)
            dialog.setWindowTitle("Авторы")
            dialog.resize(500, 400)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: rgb(248, 242, 239);
                }
            """)
            layout = QVBoxLayout(dialog)
            authors_widget = AuthorsWidget(parent=dialog)
            layout.addWidget(authors_widget)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(parent, "Ошибка открытия окна авторов", str(e))

    def get_selected_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        return selected[0].row()

    def refresh_table(self, data=None):
        if data is None:
            data, _ = fetch_all(self.table_name)

        if self.table_name == "librarians":
            data = [row for row in data if row.get("Логин") != "admin"]

        if self.table_name == "books":
            book_ids = [row["id_книги"] for row in data]

            hall_map = {}
            if book_ids:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT b.id_книги, h.Название
                    FROM books b
                    LEFT JOIN hall h ON b.id_зала = h.id_зала
                    WHERE b.id_книги IN ({})
                """.format(",".join(["%s"] * len(book_ids))), book_ids)
                for row in cur.fetchall():
                    hall_map[row["id_книги"]] = row["Название"] or ""
                conn.close()

            author_map = {}
            if book_ids:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT ba.id_книги, a.Фамилия, a.Имя
                    FROM book_authors ba
                    JOIN authors a ON ba.id_автора = a.id_автора
                    WHERE ba.id_книги IN ({})
                    ORDER BY ba.id_книги, a.Фамилия
                """.format(",".join(["%s"] * len(book_ids))), book_ids)
                for row in cur.fetchall():
                    book_id = row["id_книги"]
                    if book_id not in author_map:
                        author_map[book_id] = []
                    author_map[book_id].append(f"{row['Фамилия']} {row['Имя']}")
                conn.close()

            for row in data:
                row["id_зала"] = hall_map.get(row["id_книги"], "")
                row["Авторы"] = ", ".join(author_map.get(row["id_книги"], []))

            if "Авторы" not in self.columns:
                self.columns.append("Авторы")
                self.table.setColumnCount(len(self.columns))
                headers = [self.display_names.get(col, col) for col in self.columns]
                self.table.setHorizontalHeaderLabels(headers)

        elif self.table_name == "librarians":
            lib_ids = [row["id_библиотекаря"] for row in data]
            hall_map = {}
            if lib_ids:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT l.id_библиотекаря, h.Название
                    FROM librarians l
                    LEFT JOIN hall h ON l.id_зала = h.id_зала
                    WHERE l.id_библиотекаря IN ({})
                """.format(",".join(["%s"] * len(lib_ids))), lib_ids)
                for row in cur.fetchall():
                    hall_map[row["id_библиотекаря"]] = row["Название"] or ""
                conn.close()
            for row in data:
                row["id_зала"] = hall_map.get(row["id_библиотекаря"], "")

        elif self.table_name == "issues":
            issue_ids = [row["id_выдачи"] for row in data]
            reader_map = {}
            book_map = {}
            librarian_map = {}

            if issue_ids:
                conn = get_connection()
                cur = conn.cursor()

                cur.execute("""
                    SELECT i.id_выдачи, r.Фамилия, r.Имя, r.Отчество
                    FROM issues i
                    JOIN readers r ON i.id_читателя = r.id_читателя
                    WHERE i.id_выдачи IN ({})
                """.format(",".join(["%s"] * len(issue_ids))), issue_ids)
                for row in cur.fetchall():
                    fio = f"{row['Фамилия']} {row['Имя']}"
                    if row['Отчество']:
                        fio += f" {row['Отчество']}"
                    reader_map[row["id_выдачи"]] = fio

                cur.execute("""
                    SELECT i.id_выдачи, b.Название
                    FROM issues i
                    JOIN books b ON i.id_книги = b.id_книги
                    WHERE i.id_выдачи IN ({})
                """.format(",".join(["%s"] * len(issue_ids))), issue_ids)
                for row in cur.fetchall():
                    book_map[row["id_выдачи"]] = row["Название"]

                cur.execute("""
                    SELECT i.id_выдачи, l.Фамилия, l.Имя
                    FROM issues i
                    JOIN librarians l ON i.id_библиотекаря = l.id_библиотекаря
                    WHERE i.id_выдачи IN ({})
                """.format(",".join(["%s"] * len(issue_ids))), issue_ids)
                for row in cur.fetchall():
                    librarian_map[row["id_выдачи"]] = f"{row['Фамилия']} {row['Имя']}"

                conn.close()

            for row in data:
                row["id_читателя"] = reader_map.get(row["id_выдачи"], "—")
                row["id_книги"] = book_map.get(row["id_выдачи"], "—")
                row["id_библиотекаря"] = librarian_map.get(row["id_выдачи"], "—")

        elif self.table_name == "returns":
            return_ids = [row["id_сдачи"] for row in data]
            issue_map = {}

            if return_ids:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT r.id_сдачи,
                           CONCAT(rd.Фамилия, ' ', rd.Имя) AS reader_fio,
                           b.Название AS book_title
                    FROM returns r
                    JOIN issues i ON r.id_выдачи = i.id_выдачи
                    JOIN readers rd ON i.id_читателя = rd.id_читателя
                    JOIN books b ON i.id_книги = b.id_книги
                    WHERE r.id_сдачи IN ({})
                """.format(",".join(["%s"] * len(return_ids))), return_ids)
                for row in cur.fetchall():
                    issue_map[row["id_сдачи"]] = f"{row['reader_fio']} — {row['book_title']}"
                conn.close()

            for row in data:
                row["id_выдачи"] = issue_map.get(row["id_сдачи"], "—")

        self.table.setRowCount(0)
        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col_index, col_name in enumerate(self.columns):
                value = row_data.get(col_name, "")
                display_value = "" if value is None else str(value)

                is_date_col = col_name in ["ДатаРождения", "ДатаВыдачи", "ДатаВозврата", "ДатаСдачи"]
                if is_date_col and value:
                    try:
                        if '-' in str(value):
                            parts = str(value).split('-')
                            if len(parts) == 3:
                                formatted_date = f"{parts[2]}.{parts[1]}.{parts[0]}"
                                display_value = formatted_date
                    except:
                        pass

                item = QTableWidgetItem(str(display_value))
                if col_name in self.hidden_fields:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, col_index, item)

        if self.count_label_value:
            if self.count_sum_field:
                total = sum(row.get(self.count_sum_field, 0) or 0 for row in data)
                self.count_label_value.setText(str(total))
            else:
                self.count_label_value.setText(str(len(data)))

    def add_record(self):
        if hasattr(self, "record_dialog") and self.record_dialog is not None:
            if self.record_dialog.isVisible():
                self.record_dialog.activateWindow()
                self.record_dialog.raise_()
                return
        def save(values):
            try:
                tech_values = {}
                for key, value in values.items():
                    tech_key = HUMAN_TO_TECH.get(key, key)
                    tech_values[tech_key] = value
                values = tech_values
                if self.table_name == "books":
                    hall_id = values.pop("Зал", None)
                    if hall_id is None:
                        QMessageBox.warning(self, "Ошибка", "Выберите зал")
                        return
                    values["id_зала"] = hall_id
                    save_book(values)

                elif self.table_name == "issues":
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

                    insert_row(self.table_name, values)
                    adjust_book_count(book_id, -1)

                elif self.table_name == "returns":
                    issue_id = values.pop("Выдача", None)
                    if issue_id is None:
                        QMessageBox.warning(self, "Ошибка", "Выберите выдачу")
                        return
                    values["id_выдачи"] = issue_id
                    insert_row(self.table_name, values)
                    book_id = get_book_id_from_issue(issue_id)
                    adjust_book_count(book_id, +1)

                else:
                    hall_id = values.pop("Зал", None)
                    if hall_id is not None:
                        values["id_зала"] = hall_id
                    insert_row(self.table_name, values)

                self.refresh_table()
                if hasattr(self.window(), 'refresh_all_pages'):
                    self.window().refresh_all_pages()

                main_window = self.window()
                if (hasattr(main_window, 'home_page') and
                        hasattr(main_window.home_page, 'update_stats')):
                    main_window.home_page.update_stats()

            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Ошибка добавления записи", str(e))

        columns_with_fk = []
        for c in self.columns:
            if c == "id_зала":
                col_name = "Зал"
            elif c == "id_читателя" and self.table_name == "issues":
                col_name = "Читатель"
            elif c == "id_книги" and self.table_name == "issues":
                col_name = "Книга"
            elif c == "id_библиотекаря" and self.table_name == "issues":
                col_name = "Библиотекарь"
            elif c == "id_выдачи" and self.table_name == "returns":
                col_name = "Выдача"
            else:
                col_name = TECH_TO_HUMAN.get(c, c)
            columns_with_fk.append(col_name)

        if self.table_name == "books":
            if "Авторы" not in columns_with_fk:
                columns_with_fk.append("Авторы")
        elif self.table_name == "librarians":
            if "Зал" not in columns_with_fk:
                columns_with_fk.append("Зал")
        elif self.table_name == "issues":
            for col in ("Читатель", "Книга", "Библиотекарь"):
                if col not in columns_with_fk:
                    columns_with_fk.append(col)
        elif self.table_name == "returns":
            if "Выдача" not in columns_with_fk:
                columns_with_fk.append("Выдача")

        self.record_dialog = RecordDialog(
            columns=columns_with_fk,
            save_callback=save,
            hidden_fields=self.hidden_fields,
            close_on_save=False,
            table_name=self.table_name
        )
        self.record_dialog.show()

    def edit_record(self):
        if hasattr(self, "edit_dialog") and self.edit_dialog is not None:
            if self.edit_dialog.isVisible():
                self.edit_dialog.activateWindow()
                self.edit_dialog.raise_()
                return
        try:

            selected_items = self.table.selectedItems()
            if not selected_items:
                return

            row = selected_items[0].row()
            record_id = self.table.item(row, self.columns.index(self.primary_key)).text()
            current_values = {}

            if self.table_name == "books":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM books WHERE id_книги = %s", (record_id,))
                book_row = cur.fetchone()
                conn.close()
                if book_row:
                    current_values = {col: book_row[col] for col in self.columns if
                                      col not in ["id_книги", "Авторы", "Зал"]}
                current_values["Авторы"] = get_authors_for_book(record_id)
                current_values["Зал"] = get_hall_for_book(record_id)

            elif self.table_name == "librarians":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM librarians WHERE id_библиотекаря = %s", (record_id,))
                lib_row = cur.fetchone()
                conn.close()
                if lib_row:
                    current_values = {col: lib_row[col] for col in self.columns if
                                      col not in ["id_библиотекаря", "Зал"]}
                current_values["Зал"] = get_hall_for_librarian(record_id)

            elif self.table_name == "issues":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM issues WHERE id_выдачи = %s", (record_id,))
                issue_row = cur.fetchone()
                conn.close()
                if issue_row:
                    current_values = {col: issue_row[col] for col in self.columns if
                                      col not in ["id_выдачи", "id_читателя", "id_книги", "id_библиотекаря"]}
                current_values["Читатель"] = get_reader_for_issue(record_id)
                current_values["Книга"] = get_book_for_issue(record_id)
                current_values["Библиотекарь"] = get_librarian_for_issue(record_id)

            elif self.table_name == "returns":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM returns WHERE id_сдачи = %s", (record_id,))
                return_row = cur.fetchone()
                conn.close()
                if return_row:
                    current_values = {col: return_row[col] for col in self.columns if
                                      col not in ["id_сдачи", "id_выдачи"]}
                current_values["Выдача"] = get_issue_for_return(record_id)

            elif self.table_name == "readers":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM readers WHERE id_читателя = %s", (record_id,))
                reader_row = cur.fetchone()
                conn.close()
                if reader_row:
                    current_values = {col: reader_row[col] for col in self.columns if col != "id_читателя"}

            elif self.table_name == "hall":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM hall WHERE id_зала = %s", (record_id,))
                hall_row = cur.fetchone()
                conn.close()
                if hall_row:
                    current_values = {col: hall_row[col] for col in self.columns if col != "id_зала"}

            def save(values):
                try:
                    tech_values = {}
                    for key, value in values.items():
                        tech_key = HUMAN_TO_TECH.get(key, key)
                        tech_values[tech_key] = value
                    values = tech_values
                    if self.table_name in ("books", "librarians"):
                        hall_id = values.pop("Зал", None)
                        if hall_id is None:
                            QMessageBox.warning(
                                self,
                                "Ошибка",
                                "Выберите зал для {}".format("книги" if self.table_name == "books" else "библиотекаря")
                            )
                            return
                        values["id_зала"] = hall_id

                        # === СОХРАНЯЕМ ИЗМЕНЕНИЯ ===
                        if self.table_name == "books":
                            save_book(values, book_id=record_id)
                        else:
                            update_row(self.table_name, record_id, values, self.primary_key)

                    elif self.table_name == "issues":
                        reader_id = values.pop("Читатель", None)
                        if reader_id is None:
                            QMessageBox.warning(self, "Ошибка", "Выберите читателя")
                            return
                        values["id_читателя"] = reader_id

                        book_id = values.pop("Книга", None)
                        if book_id is None:
                            QMessageBox.warning(self, "Ошибка", "Выберите книгу")
                            return
                        values["id_книги"] = book_id

                        librarian_id = values.pop("Библиотекарь", None)
                        if librarian_id is None:
                            QMessageBox.warning(self, "Ошибка", "Выберите библиотекаря")
                            return
                        values["id_библиотекаря"] = librarian_id

                        old_book_id = get_book_id_from_issue(record_id)
                        new_book_id = book_id
                        update_row(self.table_name, record_id, values, self.primary_key)

                        if old_book_id != new_book_id:
                            if old_book_id:
                                adjust_book_count(old_book_id, +1)
                            if new_book_id:
                                conn = get_connection()
                                cur = conn.cursor()
                                cur.execute("SELECT Количество FROM books WHERE id_книги = %s", (new_book_id,))
                                row = cur.fetchone()
                                if not row or row["Количество"] <= 0:
                                    QMessageBox.warning(self, "Предупреждение",
                                                        "Новая книга недоступна, но изменения сохранены")
                                conn.close()
                                adjust_book_count(new_book_id, -1)

                    elif self.table_name == "returns":
                        issue_id = values.pop("Выдача", None)
                        if issue_id is None:
                            QMessageBox.warning(self, "Ошибка", "Выберите выдачу")
                            return
                        values["id_выдачи"] = issue_id

                        old_issue_id = None
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT id_выдачи FROM returns WHERE id_сдачи = %s", (record_id,))
                        old_row = cur.fetchone()
                        if old_row:
                            old_issue_id = old_row["id_выдачи"]
                        conn.close()

                        new_issue_id = issue_id

                        update_row(self.table_name, record_id, values, self.primary_key)

                        if old_issue_id != new_issue_id:
                            if old_issue_id:
                                old_book_id = get_book_id_from_issue(old_issue_id)
                                adjust_book_count(old_book_id, -1)  # ← МИНУС

                            if new_issue_id:
                                new_book_id = get_book_id_from_issue(new_issue_id)
                                conn = get_connection()
                                cur = conn.cursor()
                                cur.execute("SELECT Количество FROM books WHERE id_книги = %s", (new_book_id,))
                                row = cur.fetchone()
                                conn.close()
                                if not row or row["Количество"] <= 0:
                                    QMessageBox.warning(self, "Предупреждение",
                                                        "Книга из новой выдачи недоступна, но изменения сохранены")
                                adjust_book_count(new_book_id, +1)  # ← ПЛЮС

                    else:
                        update_row(self.table_name, record_id, values, self.primary_key)

                    self.refresh_table()
                    if hasattr(self.window(), 'refresh_all_pages'):
                        self.window().refresh_all_pages()

                    main_window = self.window()
                    if (hasattr(main_window, 'home_page') and
                            hasattr(main_window.home_page, 'update_stats')):
                        main_window.home_page.update_stats()

                except Exception as e_inner:
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(self, "Ошибка сохранения записи", str(e_inner))

            columns_with_fk = []
            for c in self.columns:
                if c == "id_зала":
                    col_name = "Зал"
                elif c == "id_читателя" and self.table_name == "issues":
                    col_name = "Читатель"
                elif c == "id_книги" and self.table_name == "issues":
                    col_name = "Книга"
                elif c == "id_библиотекаря" and self.table_name == "issues":
                    col_name = "Библиотекарь"
                elif c == "id_выдачи" and self.table_name == "returns":
                    col_name = "Выдача"
                elif c == "ГодИздания":
                    col_name = "Год издания"
                elif c == "ВозрастноеОграничение":
                    col_name = "Возраст"
                elif c == "ДатаВыдачи":
                    col_name = "Дата выдачи"
                elif c == "ДатаВозврата":
                    col_name = "Дата возврата"
                elif c == "ДатаРождения":
                    col_name = "Дата рождения"
                elif c == "КонтактРодителя":
                    col_name = "Контакт родителя"
                elif c == "ДатаСдачи":
                    col_name = "Дата сдачи"
                else:
                    col_name = c
                columns_with_fk.append(col_name)

            if self.table_name == "books":
                if "Авторы" not in columns_with_fk:
                    columns_with_fk.append("Авторы")
            elif self.table_name == "librarians":
                if "Зал" not in columns_with_fk:
                    columns_with_fk.append("Зал")
            elif self.table_name == "issues":
                for col in ("Читатель", "Книга", "Библиотекарь"):
                    if col not in columns_with_fk:
                        columns_with_fk.append(col)
            elif self.table_name == "returns":
                if "Выдача" not in columns_with_fk:
                    columns_with_fk.append("Выдача")

            current_values_human = {}
            for key, value in current_values.items():
                if key == "ГодИздания":
                    current_values_human["Год издания"] = value
                elif key == "ВозрастноеОграничение":
                    current_values_human["Возраст"] = value
                elif key == "ДатаВыдачи":
                    current_values_human["Дата выдачи"] = value
                elif key == "ДатаВозврата":
                    current_values_human["Дата возврата"] = value
                elif key == "ДатаРождения":
                    current_values_human["Дата рождения"] = value
                elif key == "КонтактРодителя":
                    current_values_human["Контакт родителя"] = value
                elif key == "ДатаСдачи":
                    current_values_human["Дата сдачи"] = value
                else:
                    current_values_human[key] = value

            self.edit_dialog = RecordDialog(
                columns=columns_with_fk,
                save_callback=save,
                values=current_values_human,
                hidden_fields=self.hidden_fields,
                close_on_save=True,
                table_name=self.table_name
            )
            self.edit_dialog.finished.connect(
                lambda _: setattr(self, "edit_dialog", None)
            )
            self.edit_dialog.show()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка редактирования записи", str(e))

    def delete_record(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        record_id = self.table.item(row, self.columns.index(self.primary_key)).text()

        def perform_delete():
            try:
                if self.table_name == "returns":
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT id_выдачи FROM returns WHERE id_сдачи = %s", (record_id,))
                    return_row = cur.fetchone()
                    conn.close()

                    if return_row:
                        issue_id = return_row["id_выдачи"]
                        book_id = get_book_id_from_issue(issue_id)
                        adjust_book_count(book_id, -1)

                elif self.table_name == "issues":
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) AS cnt FROM returns WHERE id_выдачи = %s", (record_id,))
                    has_return = cur.fetchone()["cnt"] > 0
                    conn.close()

                    if has_return:
                        QMessageBox.warning(
                            self,
                            "Ошибка удаления",
                            "Нельзя удалить выдачу, для которой уже есть запись о сдаче!"
                        )
                        return
                    book_id = get_book_id_from_issue(record_id)
                    adjust_book_count(book_id, +1)

                delete_row(self.table_name, record_id, self.primary_key)
                self.refresh_table()

                if hasattr(self.window(), 'refresh_all_pages'):
                    self.window().refresh_all_pages()

                main_window = self.window()
                if (hasattr(main_window, 'home_page') and
                        hasattr(main_window.home_page, 'update_stats')):
                    main_window.home_page.update_stats()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка удаления", str(e))

        dialog = ConfirmDeleteDialog(confirm_callback=perform_delete)
        dialog.exec()

def save_book(values, book_id=None):
    conn = get_connection()
    cur = conn.cursor()

    authors_ids = values.pop("Авторы", [])
    hall_id = values.pop("id_зала", None)

    if book_id is None:
        cur.execute(
            """
            INSERT INTO books (Название, Жанр, ГодИздания, ВозрастноеОграничение, ISBN, ББК, Количество, id_зала)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                values["Название"],
                values.get("Жанр"),
                values.get("ГодИздания"),
                values["ВозрастноеОграничение"],
                values["ISBN"],
                values.get("ББК"),
                values.get("Количество"),
                hall_id
            )
        )
        book_id = cur.lastrowid
    else:
        cur.execute(
            """
            UPDATE books SET Название=%s, Жанр=%s, ГодИздания=%s, ВозрастноеОграничение=%s, ISBN=%s, ББК=%s,  
             Количество=%s, id_зала=%s
            WHERE id_книги=%s
            """,
            (
                values["Название"],
                values.get("Жанр"),
                values.get("ГодИздания"),
                values["ВозрастноеОграничение"],
                values["ISBN"],
                values.get("ББК"),
                values.get("Количество"),
                hall_id,
                book_id
            )
        )
        cur.execute("DELETE FROM book_authors WHERE id_книги=%s", (book_id,))

    for author_id in authors_ids:
        cur.execute(
            "INSERT INTO book_authors (id_книги, id_автора) VALUES (%s, %s)",
            (book_id, author_id)
        )

    conn.commit()
    conn.close()

def get_authors_for_book(book_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.id_автора, a.Фамилия, a.Имя
        FROM authors a
        JOIN book_authors ba ON a.id_автора = ba.id_автора
        WHERE ba.id_книги = %s
        """,
        (book_id,)
    )
    rows = cur.fetchall()
    conn.close()

    authors = []
    for row in rows:
        if isinstance(row, dict):
            authors.append({
                "id_автора": row["id_автора"],
                "Фамилия": row["Фамилия"],
                "Имя": row["Имя"]
            })
        else:
            authors.append({
                "id_автора": row[0],
                "Фамилия": row[1],
                "Имя": row[2]
            })
    return authors

def get_hall_for_book(book_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT h.id_зала, h.Название FROM hall h "
        "JOIN books b ON h.id_зала = b.id_зала "
        "WHERE b.id_книги = %s",
        (book_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id_зала": row["id_зала"], "Название": row["Название"]}
    return None
def get_hall_for_librarian(librarian_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT h.id_зала, h.Название FROM hall h "
        "JOIN librarians l ON h.id_зала = l.id_зала "
        "WHERE l.id_библиотекаря = %s",
        (librarian_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id_зала": row["id_зала"], "Название": row["Название"]}
    return None

def get_reader_for_issue(issue_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id_читателя, r.Фамилия, r.Имя
        FROM readers r
        JOIN issues i ON r.id_читателя = i.id_читателя
        WHERE i.id_выдачи = %s
        """,
        (issue_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id_читателя": row["id_читателя"],
            "ФИО": f"{row['Фамилия']} {row['Имя']}"
        }
    return None

def get_book_for_issue(issue_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.id_книги, b.Название
        FROM books b
        JOIN issues i ON b.id_книги = i.id_книги
        WHERE i.id_выдачи = %s
        """,
        (issue_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        authors_list = get_authors_for_book(row['id_книги'])
        return {
            "id_книги": row["id_книги"],
            "Название": row["Название"],
            "Авторы": authors_list
        }
    return None

def get_librarian_for_issue(issue_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.id_библиотекаря, l.Фамилия, l.Имя
        FROM librarians l
        JOIN issues i ON l.id_библиотекаря = i.id_библиотекаря
        WHERE i.id_выдачи = %s
        """,
        (issue_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id_библиотекаря": row["id_библиотекаря"],
            "ФИО": f"{row['Фамилия']} {row['Имя']}"
        }
    return None

def get_issue_for_return(return_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            r.id_выдачи,
            rd.Фамилия AS reader_surname,
            b.Название AS book_title
        FROM returns r
        JOIN issues i ON r.id_выдачи = i.id_выдачи
        JOIN readers rd ON i.id_читателя = rd.id_читателя
        JOIN books b ON i.id_книги = b.id_книги
        WHERE r.id_сдачи = %s
        """,
        (return_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        display_text = f"{row['reader_surname']} — {row['book_title']}"
        return {
            "id_выдачи": row["id_выдачи"],
            "display_text": display_text
        }
    return None

def get_book_id_from_issue(issue_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_книги FROM issues WHERE id_выдачи = %s", (issue_id,))
    row = cur.fetchone()
    conn.close()
    return row["id_книги"] if row else None

def adjust_book_count(book_id, delta):
    if book_id is None:
        return
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE books SET Количество = Количество + %s WHERE id_книги = %s", (delta, book_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при изменении количества книги {book_id}: {e}")