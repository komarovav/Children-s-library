from PyQt6.QtWidgets import (QWidget, QDialog, QHeaderView, QHBoxLayout, QVBoxLayout,
                             QTableWidget, QLabel, QTableWidgetItem, QPushButton,
                             QLineEdit, QMessageBox, QStyledItemDelegate, QLineEdit)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize, Qt
from dialogs import RecordDialog, ConfirmDeleteDialog
from repository import fetch_all, insert_row, update_row, delete_row
from db import get_connection

class Field(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setFrame(False)
        editor.setAutoFillBackground(True)
        editor.setStyleSheet("background-color: white; color: rgb(27, 71, 93); padding: 5px;")
        editor.setMinimumHeight(option.rect.height())
        return editor

    def setEditorData(self, editor, index):
        value = index.data()
        editor.setText(str(value) if value is not None else "")

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

        # Таблица
        self.table = QTableWidget()
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
        """)
        self.table.setEditTriggers(QTableWidget.EditTrigger.SelectedClicked)  # редактирование только выбранной строки по клику
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(35)  # увеличиваем высоту строки
        self.layout.addWidget(self.table)

        # Кнопки
        buttons_layout = QHBoxLayout()
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
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        self.layout.addLayout(buttons_layout)

        self.delete_btn.clicked.connect(self.delete_author_row)
        self.save_btn.clicked.connect(self.save_authors)

        self.load_authors()
        self.add_empty_row()

    def load_authors(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {self.table_name}")
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
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки авторов", str(e))

    def add_empty_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            self.table.setItem(row, col, item)
            if col == 0:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

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
                        "INSERT INTO authors (id_автора, Фамилия, Имя, Отчество) VALUES (%s, %s, %s, %s)",
                        (pk_value, row_data["Фамилия"], row_data["Имя"], row_data["Отчество"])
                    )
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
                 search_columns: list[str] | None = None, hidden_fields=None):
        super().__init__()
        self.table_name = table_name
        self.primary_key = primary_key
        self.columns = columns
        self.search_columns = search_columns or []
        self.hidden_fields = hidden_fields or []
        # Поиск
        self.search_input = QLineEdit(self)
        self.search_input.textChanged.connect(self.on_search)
        self.search_input.setPlaceholderText(f"Поиск: {title.lower()}...")
        self.search_input.setFont(QFont("AG_CenturyOldStyle", 18))
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

        # Заголовок
        label = QLabel(title, self)
        label.setFont(QFont("AG_CenturyOldStyle", 18))
        label.setStyleSheet("color: rgb(27, 71, 93);")
        label.setGeometry(0, 48, 200, 40)

        # Таблица
        self.table = QTableWidget(self)
        header = self.table.horizontalHeader()

        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setGeometry(0, 80, 870, 595)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; color: rgb(27, 71, 93);
                border: 2px solid rgb(179, 195, 208); border-radius: 5px; gridline-color: rgb(179, 195, 208);}
            QHeaderView::section { background-color: rgb(179, 195, 208);
                color: rgb(27, 71, 93); padding: 5px; font-size: 18px; }
            QTableWidget::item { padding: 10px; }
        """)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

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
                border-radius: 10px;  /* скругление всей кнопки */
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
            btn_author = QPushButton("Продлить", self)
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

        btn_edit = QPushButton(self)
        btn_edit.setIcon(QIcon("edit.png"))
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
        btn_delete.setIcon(QIcon("delete.png"))
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

    def on_search(self, text: str):
        text = text.strip().lower()

        if not text:
            self.refresh_table()
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

        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, col in enumerate(self.columns):
                val = row[col] if isinstance(row, dict) else row[c]
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

        if self.count_label_value:
            self.count_label_value.setText(str(len(data)))

    def add_record(self):
        def save(values):
            insert_row(self.table_name, values)
            self.refresh_table()

        self.record_dialog = RecordDialog(
            self.columns,
            save_callback=save,
            hidden_fields=self.hidden_fields,
            close_on_save=False
        )
        self.record_dialog.show()

    def edit_record(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        record_id = self.table.item(row, self.columns.index(self.primary_key)).text()

        current_values = {
            col: self.table.item(row, self.columns.index(col)).text()
            for col in self.columns
        }

        def save(values):
            update_row(self.table_name, record_id, values, self.primary_key)
            self.refresh_table()

        self.edit_dialog = RecordDialog(
            self.columns,
            save_callback=save,
            values=current_values,
            hidden_fields=self.hidden_fields,
            close_on_save=True
        )
        self.edit_dialog.show()

    def delete_record(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        record_id = self.table.item(row, self.columns.index(self.primary_key)).text()

        def confirm_delete():
            delete_row(self.table_name, record_id, self.primary_key)
            self.refresh_table()

        dialog = ConfirmDeleteDialog(confirm_callback=confirm_delete)
        dialog.exec()
