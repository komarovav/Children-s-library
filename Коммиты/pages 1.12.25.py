from PyQt6.QtWidgets import QWidget, QTableWidget, QLabel, QTableWidgetItem, QPushButton, QLineEdit, QMessageBox
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize
from dialogs import RecordDialog
from repository import fetch_all, insert_row, update_row, delete_row

class PageTemplate(QWidget):
    def __init__(self, title: str, columns: list[str], data: list[dict], table_name: str, primary_key: str = "id"):
        super().__init__()
        self.table_name = table_name
        self.primary_key = primary_key
        self.columns = columns

        # Поиск
        self.search_input = QLineEdit(self)
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

        label_role = QLabel("Администратор", self)
        label_role.setFont(QFont("AG_CenturyOldStyle", 18))
        label_role.setStyleSheet("color: rgb(27, 71, 93);")
        label_role.setGeometry(1015, 595, 200, 40)

        # Таблица
        self.table = QTableWidget(self)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setGeometry(0, 80, 870, 595)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; color: rgb(27, 71, 93);
                border: 2px solid rgb(179, 195, 208); border-radius: 5px; gridline-color: rgb(179, 195, 208);}
            QHeaderView::section { background-color: rgb(179, 195, 208);
                color: rgb(27, 71, 93); padding: 5px; font-size: 18px; }
            QTableWidget::item { padding: 10px; }
        """)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

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
        # Кнопка "+Автор" ТОЛЬКО для книг
        if self.table_name == "books":
            btn_author = QPushButton("+Автор", self)
            btn_author.setFont(QFont("AG_CenturyOldStyle", 16))
            btn_author.setGeometry(997, 140, 160, 50)
            btn_author.clicked.connect(self.open_authors)

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

        # Подключение кнопок
        btn_add.clicked.connect(self.add_record)
        btn_edit.clicked.connect(self.edit_record)
        btn_delete.clicked.connect(self.delete_record)

        self.refresh_table(data)

    def open_authors(self):
        from windows import AuthorsDialog
        dialog = AuthorsDialog()
        dialog.exec()

    def get_selected_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        return selected[0].row()

    def refresh_table(self, data=None):
        if data is None:
            data, _ = fetch_all(self.table_name)  # ожидается list[dict]
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, col in enumerate(self.columns):
                val = row[col] if isinstance(row, dict) else row[c]
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    def add_record(self):
        dialog = RecordDialog(self.columns)
        if dialog.exec():
            values = dialog.get_values()
            insert_row(self.table_name, values)
            self.refresh_table()

    def edit_record(self):
        row_index = self.get_selected_row()
        if row_index is None:
            msg = QMessageBox(self)
            msg.setWindowTitle("Ошибка")
            msg.setText("Выберите запись для редактирования")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStyleSheet("""
                QLabel { color: black; font-size: 16px; }
                QPushButton { color: black; background-color: rgb(200,200,200); padding: 5px 15px; border-radius: 5px; }
            """)
            msg.exec()
            return

        id_col_idx = self.columns.index(self.primary_key)
        record_id_item = self.table.item(row_index, id_col_idx)
        if not record_id_item:
            msg = QMessageBox(self)
            msg.setWindowTitle("Ошибка")
            msg.setText("Невозможно определить ID записи")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStyleSheet("""
                QLabel { color: black; font-size: 16px; }
                QPushButton { color: black; background-color: rgb(200,200,200); padding: 5px 15px; border-radius: 5px; }
            """)
            msg.exec()
            return

        record_id_text = record_id_item.text()
        try:
            record_id = int(record_id_text)
        except ValueError:
            record_id = record_id_text

        current_values = {}
        for i, col in enumerate(self.columns):
            item = self.table.item(row_index, i)
            current_values[col] = item.text() if item else ""

        dialog = RecordDialog(self.columns, current_values)
        if dialog.exec():
            values = dialog.get_values()
            for k, v in values.items():
                if v == "":
                    values[k] = None

            try:
                update_row(self.table_name, record_id, values, self.primary_key)
            except Exception as e:
                msg = QMessageBox(self)
                msg.setWindowTitle("Ошибка")
                msg.setText(f"Не удалось обновить запись:\n{e}")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setStyleSheet("""
                    QLabel { color: black; font-size: 16px; }
                    QPushButton { color: black; background-color: rgb(200,200,200); padding: 5px 15px; border-radius: 5px; }
                """)
                msg.exec()
                return

            self.refresh_table()

    def delete_record(self):
        row_index = self.get_selected_row()
        if row_index is None:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        id_col_idx = self.columns.index(self.primary_key)
        record_id_item = self.table.item(row_index, id_col_idx)
        if not record_id_item:
            QMessageBox.warning(self, "Ошибка", "Невозможно определить ID записи")
            return
        record_id = record_id_item.text()

        reply = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить запись {record_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_row(self.table_name, record_id, self.primary_key)
            self.refresh_table()