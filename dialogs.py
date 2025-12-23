from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QWidget, QScrollArea, QListWidget, QListWidgetItem, QMessageBox, QDateEdit
)
from PyQt6.QtGui import (QIntValidator, QRegularExpressionValidator, QValidator)
from PyQt6.QtCore import Qt, QDate, QRegularExpression
from db import get_connection
REQUIRED_FIELDS = {
    "books": {"Название", "Возрастное ограничение", "ISBN", "ББК", "Количество"},
    "librarians": {"Логин", "Пароль", "Фамилия", "Имя"},
    "issues": {"Дата выдачи", "Дата возврата"},
    "returns": {"Дата сдачи"},
    "readers": {"Фамилия", "Имя", "Контакт родителя"},
    "hall": {"Название"},
}


class PositiveIntValidator(QValidator):
    def validate(self, input_str: str, pos: int):
        if not input_str:
            return QValidator.State.Intermediate, input_str, pos

        if not input_str.isdigit():
            return QValidator.State.Invalid, input_str, pos

        num = int(input_str)
        if num < 1 or num > 99999:
            return QValidator.State.Invalid, input_str, pos

        return QValidator.State.Acceptable, input_str, pos
class IssueSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Введите фамилию, название книги или ISBN")
        self.search.setMinimumHeight(36)
        self.search.setFixedWidth(600)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)
        self.results = QListWidget()
        self.results.setMinimumHeight(36)
        self.results.setFixedWidth(600)
        self.results.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)
        self.selected_label = QLabel("Выбранная выдача:")
        self.selected_label.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        self.selected = QListWidget()
        self.selected.setMinimumHeight(36)
        self.selected.setFixedWidth(600)
        self.selected.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.search)
        layout.addWidget(self.results)
        layout.addWidget(self.selected_label)
        layout.addWidget(self.selected)

        self.search.textChanged.connect(self.search_issues)
        self.results.itemDoubleClicked.connect(self.select_issue)

    def search_issues(self, text):
        self.results.clear()
        if not text.strip():
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                i.id_выдачи,
                CONCAT(r.Фамилия, ' ', r.Имя, 
                       CASE WHEN r.Отчество IS NOT NULL THEN CONCAT(' ', r.Отчество) ELSE '' END
                ) AS reader_fio,
                b.Название AS book_title
            FROM issues i
            JOIN readers r ON i.id_читателя = r.id_читателя
            JOIN books b ON i.id_книги = b.id_книги
            WHERE 
                (r.Фамилия LIKE %s OR r.Имя LIKE %s OR 
                 b.Название LIKE %s OR b.ISBN LIKE %s)
                -- Только НЕ сданные книги
                AND i.id_выдачи NOT IN (SELECT id_выдачи FROM returns)
            ORDER BY r.Фамилия, b.Название
        """, (f"%{text}%", f"%{text}%", f"%{text}%", f"%{text}%"))

        rows = cur.fetchall()
        conn.close()

        for row in rows:
            display_text = f"{row['reader_fio']} — {row['book_title']}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, row['id_выдачи'])
            self.results.addItem(item)

    def select_issue(self, item):
        self.selected.clear()
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
        self.selected.addItem(new_item)

    def get_selected_id(self):
        if self.selected.count() == 0:
            if hasattr(self, "initial_id") and self.initial_id:
                return self.initial_id
            return None
        return self.selected.item(0).data(Qt.ItemDataRole.UserRole)

    def set_selected(self, issue_info):
        if isinstance(issue_info, dict) and "id_выдачи" in issue_info:
            issue_id = issue_info["id_выдачи"]
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    i.id_выдачи,
                    r.Фамилия, r.Имя,
                    b.Название, b.ISBN
                FROM issues i
                JOIN readers r ON i.id_читателя = r.id_читателя
                JOIN books b ON i.id_книги = b.id_книги
                WHERE i.id_выдачи = %s
            """, (issue_id,))
            row = cur.fetchone()
            conn.close()

            if row:
                display_text = f"#{row['id_выдачи']} | {row['Фамилия']} {row['Имя']} — {row['Название']} ({row['ISBN']})"
                self.selected.clear()
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, row['id_выдачи'])
                self.selected.addItem(item)
                self.initial_id = row['id_выдачи']

    def clear(self):
        if hasattr(self, 'search') and self.search is not None:
            self.search.clear()
        if hasattr(self, 'results') and self.results is not None:
            self.results.clear()
        if hasattr(self, 'selected') and self.selected is not None:
            self.selected.clear()
        if hasattr(self, 'initial_id'):
            delattr(self, 'initial_id')

class BookSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Введите ISBN, название или автора")
        self.search.setMinimumHeight(36)
        self.search.setFixedWidth(600)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.results = QListWidget()
        self.results.setMinimumHeight(36)
        self.results.setFixedWidth(600)
        self.results.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.selected_label = QLabel("Выбранная книга:")
        self.selected_label.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        self.selected = QListWidget()
        self.selected.setMinimumHeight(36)
        self.selected.setFixedWidth(600)
        self.selected.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.search)
        layout.addWidget(self.results)
        layout.addWidget(self.selected_label)
        layout.addWidget(self.selected)

        self.search.textChanged.connect(self.search_books)
        self.results.itemDoubleClicked.connect(self.select_book)

    def search_books(self, text):
        self.results.clear()
        if not text.strip() or len(text.strip()) < 2:
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                b.id_книги, 
                b.Название, 
                b.ISBN,
                a.id_автора,
                a.Фамилия,
                a.Имя
            FROM books b
            LEFT JOIN book_authors ba ON b.id_книги = ba.id_книги
            LEFT JOIN authors a ON ba.id_автора = a.id_автора
            WHERE 
                b.Количество > 0  -- ← ТОЛЬКО КНИГИ В НАЛИЧИИ!
                AND (
                    b.Название LIKE %s 
                    OR b.ISBN LIKE %s 
                    OR a.Фамилия LIKE %s 
                    OR a.Имя LIKE %s
                )
            ORDER BY b.Название, a.Фамилия
        """, (f"%{text}%", f"%{text}%", f"%{text}%", f"%{text}%"))

        rows = cur.fetchall()
        conn.close()

        books_dict = {}
        for row in rows:
            book_id = row["id_книги"]
            if book_id not in books_dict:
                books_dict[book_id] = {
                    'id_книги': book_id,
                    'Название': row["Название"],
                    'ISBN': row["ISBN"],
                    'Авторы': []
                }
            if row["Фамилия"] and row["Имя"]:
                books_dict[book_id]['Авторы'].append(f"{row['Фамилия']} {row['Имя']}")

        for book in books_dict.values():
            author_str = ", ".join(book['Авторы']) if book['Авторы'] else "Неизвестен"
            display_text = f"{book['Название']} — {author_str}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, book['id_книги'])
            self.results.addItem(item)

    def select_book(self, item):
        self.selected.clear()
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
        self.selected.addItem(new_item)

    def get_selected_id(self):
        if self.selected.count() == 0:
            if hasattr(self, "initial_id") and self.initial_id:
                return self.initial_id
            return None
        return self.selected.item(0).data(Qt.ItemDataRole.UserRole)

    def set_selected(self, book):
        authors_str = ", ".join(f"{a['Фамилия']} {a['Имя']}" for a in book.get("Авторы", []))
        display_text = f"{book['Название']} — {authors_str}" if authors_str else book['Название']
        self.selected.clear()
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, book['id_книги'])
        self.selected.addItem(item)
        self.initial_id = book['id_книги']

    def clear(self):
        if hasattr(self, 'search') and self.search is not None:
            self.search.clear()
        if hasattr(self, 'results') and self.results is not None:
            self.results.clear()
        if hasattr(self, 'selected') and self.selected is not None:
            self.selected.clear()
        if hasattr(self, 'initial_id'):
            delattr(self, 'initial_id')

class ReaderSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Введите фамилию читателя")
        self.search.setMinimumHeight(36)
        self.search.setFixedWidth(600)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.results = QListWidget()
        self.results.setMinimumHeight(36)
        self.results.setFixedWidth(600)
        self.results.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.selected_label = QLabel("Выбранный читатель:")
        self.selected_label.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        self.selected = QListWidget()
        self.selected.setMinimumHeight(36)
        self.selected.setFixedWidth(600)
        self.selected.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.search)
        layout.addWidget(self.results)
        layout.addWidget(self.selected_label)
        layout.addWidget(self.selected)

        self.search.textChanged.connect(self.search_readers)
        self.results.itemDoubleClicked.connect(self.select_reader)

    def search_readers(self, text):
        self.results.clear()
        if not text.strip():
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id_читателя, Фамилия, Имя, Отчество FROM readers "
            "WHERE Фамилия LIKE %s ORDER BY Фамилия, Имя",
            (f"%{text}%",)
        )
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            fio = f"{row['Фамилия']} {row['Имя']} {row['Отчество']}".strip()
            item = QListWidgetItem(fio)
            item.setData(Qt.ItemDataRole.UserRole, row['id_читателя'])
            self.results.addItem(item)

    def select_reader(self, item):
        self.selected.clear()
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
        self.selected.addItem(new_item)

    def get_selected_id(self):
        if self.selected.count() == 0:
            if hasattr(self, "initial_id") and self.initial_id:
                return self.initial_id
            return None
        return self.selected.item(0).data(Qt.ItemDataRole.UserRole)

    def set_selected(self, reader):
        self.selected.clear()
        item = QListWidgetItem(reader['ФИО'])
        item.setData(Qt.ItemDataRole.UserRole, reader['id_читателя'])
        self.selected.addItem(item)
        self.initial_id = reader['id_читателя']

    def clear(self):
        # Очищаем поле поиска
        if hasattr(self, 'search') and self.search is not None:
            self.search.clear()
        if hasattr(self, 'results') and self.results is not None:
            self.results.clear()
        if hasattr(self, 'selected') and self.selected is not None:
            self.selected.clear()
        if hasattr(self, 'initial_id'):
            delattr(self, 'initial_id')

class LibrarianSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Введите фамилию библиотекаря")
        self.search.setMinimumHeight(36)
        self.search.setFixedWidth(600)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.results = QListWidget()
        self.results.setMinimumHeight(36)
        self.results.setFixedWidth(600)
        self.results.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.selected_label = QLabel("Выбранный библиотекарь:")
        self.selected_label.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        self.selected = QListWidget()
        self.selected.setMinimumHeight(36)
        self.selected.setFixedWidth(600)
        self.selected.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.search)
        layout.addWidget(self.results)
        layout.addWidget(self.selected_label)
        layout.addWidget(self.selected)

        self.search.textChanged.connect(self.search_librarians)
        self.results.itemDoubleClicked.connect(self.select_librarian)

    def search_librarians(self, text):
        self.results.clear()
        if not text.strip():
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_библиотекаря, Фамилия, Имя, Отчество 
            FROM librarians 
            WHERE 
                id_библиотекаря != 'admin'
                AND (
                    Фамилия LIKE %(search)s
                    OR Имя LIKE %(search)s
                    OR Отчество LIKE %(search)s
                )
            ORDER BY Фамилия, Имя
            """,
            {"search": f"%{text}%"}
        )
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            fio = f"{row['Фамилия']} {row['Имя']} {row['Отчество']}".strip()
            item = QListWidgetItem(fio)
            item.setData(Qt.ItemDataRole.UserRole, row['id_библиотекаря'])
            self.results.addItem(item)

    def select_librarian(self, item):
        self.selected.clear()
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
        self.selected.addItem(new_item)

    def get_selected_id(self):
        if self.selected.count() == 0:
            if hasattr(self, "initial_id") and self.initial_id:
                return self.initial_id
            return None
        return self.selected.item(0).data(Qt.ItemDataRole.UserRole)

    def set_selected(self, librarian):
        self.selected.clear()
        item = QListWidgetItem(librarian['ФИО'])
        item.setData(Qt.ItemDataRole.UserRole, librarian['id_библиотекаря'])
        self.selected.addItem(item)
        self.initial_id = librarian['id_библиотекаря']

    def clear(self):
        if hasattr(self, 'search') and self.search is not None:
            self.search.clear()
        if hasattr(self, 'results') and self.results is not None:
            self.results.clear()
        if hasattr(self, 'selected') and self.selected is not None:
            self.selected.clear()
        if hasattr(self, 'initial_id'):
            delattr(self, 'initial_id')

class HallSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Введите название зала")
        self.search.setMinimumHeight(36)
        self.search.setFixedWidth(600)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.results = QListWidget()
        self.results.setMinimumHeight(36)
        self.results.setFixedWidth(600)
        self.results.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.selected_label = QLabel("Выбранный зал:")
        self.selected_label.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        self.selected = QListWidget()
        self.selected.setMinimumHeight(36)
        self.selected.setFixedWidth(600)
        self.selected.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.search)
        layout.addWidget(self.results)
        layout.addWidget(self.selected_label)
        layout.addWidget(self.selected)

        self.search.textChanged.connect(self.search_halls)
        self.results.itemDoubleClicked.connect(self.select_hall)

    def search_halls(self, text):
        self.results.clear()
        if not text.strip():
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id_зала, Название FROM hall WHERE Название LIKE %s ORDER BY Название",
            (f"%{text}%",)
        )
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            item = QListWidgetItem(row['Название'])
            item.setData(Qt.ItemDataRole.UserRole, row['id_зала'])
            self.results.addItem(item)

    def select_hall(self, item):
        self.selected.clear()
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
        self.selected.addItem(new_item)

    def get_selected_id(self):
        if self.selected.count() == 0:
            if hasattr(self, "initial_id") and self.initial_id:
                return self.initial_id
            return None
        return self.selected.item(0).data(Qt.ItemDataRole.UserRole)

    def set_selected(self, hall):
        self.selected.clear()
        item = QListWidgetItem(hall['Название'])
        item.setData(Qt.ItemDataRole.UserRole, hall['id_зала'])
        self.selected.addItem(item)
        self.initial_id = hall['id_зала']

    def clear(self):
        if hasattr(self, 'search') and self.search is not None:
            self.search.clear()
        if hasattr(self, 'results') and self.results is not None:
            self.results.clear()
        if hasattr(self, 'selected') and self.selected is not None:
            self.selected.clear()
        if hasattr(self, 'initial_id'):
            delattr(self, 'initial_id')

class AuthorsSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Введите фамилию автора")
        self.search.setMinimumHeight(36)
        self.search.setFixedWidth(600)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.results = QListWidget()
        self.results.setMinimumHeight(36)
        self.results.setFixedWidth(600)
        self.results.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border: 1px solid rgb(179, 195, 208);             
                border-radius: 10px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        self.selected = QListWidget()
        self.selected.setMinimumHeight(36)
        self.selected.setFixedWidth(600)
        self.selected.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);
                border: 1px solid rgb(179, 195, 208);
                border-radius: 10px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        layout.addWidget(self.search)

        layout.addWidget(self.results)

        selected_label = QLabel("Выбраны")
        selected_label.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        layout.addWidget(selected_label)

        self.selected.setStyleSheet("""
            QListWidget {
                background-color: rgb(179, 195, 208);  /* более светлый фон */
                border-radius: 5px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
        """)
        self.selected.setAutoFillBackground(True)
        self.selected.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout.addWidget(self.selected)

        self.search.textChanged.connect(self.search_authors)
        self.results.itemDoubleClicked.connect(self.add_author)
        self.selected.itemDoubleClicked.connect(self.remove_author)

        self.results.setAutoFillBackground(True)
        self.selected.setAutoFillBackground(True)
        self.setAutoFillBackground(True)

    def search_authors(self, text):
        self.results.clear()
        if not text.strip():
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_автора, Фамилия, Имя
            FROM authors
            WHERE Фамилия LIKE %s
            ORDER BY Фамилия
            """,
            (f"%{text}%",)
        )
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            item = QListWidgetItem(f"{row['Фамилия']} {row['Имя']}")
            item.setData(Qt.ItemDataRole.UserRole, row["id_автора"])
            self.results.addItem(item)

    def add_author(self, item):
        author_id = item.data(Qt.ItemDataRole.UserRole)
        for i in range(self.selected.count()):
            if self.selected.item(i).data(Qt.ItemDataRole.UserRole) == author_id:
                return
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.ItemDataRole.UserRole, author_id)
        self.selected.addItem(new_item)

    def remove_author(self, item):
        self.selected.takeItem(self.selected.row(item))

    def get_selected_ids(self):
        return [self.selected.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.selected.count())]

    def set_selected(self, authors):
        self.selected.clear()
        for a in authors:
            item = QListWidgetItem(f"{a['Фамилия']} {a['Имя']}")
            item.setData(Qt.ItemDataRole.UserRole, a["id_автора"])
            self.selected.addItem(item)

    def clear(self):
        if hasattr(self, 'search') and self.search is not None:
            self.search.clear()
        if hasattr(self, 'results') and self.results is not None:
            self.results.clear()
        if hasattr(self, 'selected') and self.selected is not None:
            self.selected.clear()
        if hasattr(self, 'initial_id'):
            delattr(self, 'initial_id')

class RenewalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Продлить выдачу")
        self.resize(600, 300)
        self.setStyleSheet("background-color: rgb(248, 242, 239);")

        layout = QVBoxLayout(self)

        label1 = QLabel("Выберите выдачу:")
        label1.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        layout.addWidget(label1)

        self.issue_selector = IssueSelector()
        layout.addWidget(self.issue_selector)

        label2 = QLabel("Новая дата возврата:")
        label2.setStyleSheet("color: rgb(27, 71, 93); font-size: 14px;")
        layout.addWidget(label2)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumHeight(36)
        self.date_edit.setFixedWidth(120)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background-color: rgb(179, 195, 208);
                border: none;
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(27, 71, 93);
                font-size: 14px;
            }
            QDateEdit::drop-down {
                width: 0px;  /* скрываем стрелку */
            }
        """)
        layout.addWidget(self.date_edit)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Продлить")
        self.cancel_btn = QPushButton("Отмена")

        button_style = """
            QPushButton {
                background-color: rgb(179, 195, 208);
                border: none;
                color: rgb(27, 71, 93);
                border-radius: 10px;
                font-size: 14px;
                padding: 8px 16px;  /* ← ВЕРТИКАЛЬНЫЙ и ГОРИЗОНТАЛЬНЫЙ отступ */
            }
            QPushButton:hover {
                background-color: rgb(200, 210, 220);
            }
        """

        self.save_btn.setStyleSheet(button_style)
        self.cancel_btn.setStyleSheet(button_style)

        self.save_btn.setFixedSize(120, 40)
        self.cancel_btn.setFixedSize(120, 40)

        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.accept)

        self.issue_selector.results.itemDoubleClicked.connect(self.on_issue_selected)

    def on_issue_selected(self, item=None):
        issue_id = self.issue_selector.get_selected_id()
        if not issue_id:
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT ДатаВозврата 
                FROM issues 
                WHERE id_выдачи = %s
            """, (issue_id,))
            row = cur.fetchone()
            conn.close()

            if row and row['ДатаВозврата']:
                from datetime import datetime
                date_obj = datetime.strptime(str(row['ДатаВозврата']), '%Y-%m-%d')
                self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            else:
                self.date_edit.setDate(QDate.currentDate())

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить дату: {e}")
            self.date_edit.setDate(QDate.currentDate())

    def get_renewal_data(self):
        return {
            'issue_id': self.issue_selector.get_selected_id(),
            'new_return_date': self.date_edit.date().toString("yyyy-MM-dd")
        }

class RecordDialog(QDialog):
    def __init__(self, columns, save_callback, values=None, hidden_fields=None,
                 close_on_save=False, table_name=None, display_names=None):
        super().__init__()
        self.columns = columns
        self.save_callback = save_callback
        self.values = values or {}
        self.hidden_fields = hidden_fields or []
        self.close_on_save = close_on_save
        self.table_name = table_name
        self.display_names = display_names or {}
        self.inputs = {}
        self.required_fields = REQUIRED_FIELDS.get(table_name, set())
        self.error_labels = {}

        self.resize(700, 350)
        self.setStyleSheet("""
            QDialog { background-color: rgb(248, 242, 239); }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 20)
        main_layout.setSpacing(20)

        form_widget = QWidget()
        form_widget.setAutoFillBackground(True)
        form_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        form_widget.setStyleSheet("background-color: rgb(248, 242, 239);")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)
        DATE_COLUMNS = {"Дата рождения", "Дата выдачи", "Дата возврата", "Дата сдачи"}

        for col in self.columns:
            error_label = QLabel("")
            error_label.setStyleSheet("color: red; font-size: 12px;")
            error_label.hide()
            self.error_labels[col] = error_label
            if col in self.hidden_fields:
                continue

            label_text = self.display_names.get(col.rstrip(" *"), col)
            label = QLabel(label_text)
            label.setStyleSheet("QLabel { color: rgb(27, 71, 93); font-size: 14px; }")

            if col in DATE_COLUMNS:
                edit = QDateEdit()
                edit.setCalendarPopup(True)
                edit.setDisplayFormat("dd.MM.yyyy")
                edit.setMinimumHeight(36)
                edit.setFixedWidth(100)

                edit.setStyleSheet("""
                     QDateEdit {
                         background-color: rgb(179, 195, 208);
                         border: none;
                         border-radius: 5px;
                         padding-left: 10px;
                         color: rgb(27, 71, 93);   
                         font-size: 14px;
                     }
                     QDateEdit::drop-down {
                         width: 0px;            
                     }
                 """)

                if col in self.values and self.values[col]:
                    try:
                        parts = str(self.values[col]).split('-')
                        if len(parts) == 3:
                            edit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
                    except (ValueError, TypeError, AttributeError):
                        pass
                else:
                    edit.setDate(QDate.currentDate())

            elif self.table_name == "books" and col == "Авторы":
                edit = AuthorsSelector()
                if "Авторы" in self.values:
                    edit.set_selected(self.values["Авторы"])

            elif self.table_name in ("books", "librarians") and col == "Зал":
                edit = HallSelector()
                hall_info = self.values.get("Зал")
                if hall_info and isinstance(hall_info, dict):
                    edit.set_selected(hall_info)

            elif self.table_name == "issues" and col == "Читатель":
                edit = ReaderSelector()
                reader_info = self.values.get("Читатель")
                if reader_info and isinstance(reader_info, dict):
                    edit.set_selected(reader_info)

            elif self.table_name == "issues" and col == "Книга":
                edit = BookSelector()
                book_info = self.values.get("Книга")
                if book_info and isinstance(book_info, dict):
                    edit.set_selected(book_info)

            elif self.table_name == "issues" and col == "Библиотекарь":
                edit = LibrarianSelector()
                librarian_info = self.values.get("Библиотекарь")
                if librarian_info and isinstance(librarian_info, dict):
                    edit.set_selected(librarian_info)

            elif self.table_name == "returns" and col == "Выдача":
                edit = IssueSelector()
                issue_info = self.values.get("Выдача")
                if issue_info and isinstance(issue_info, dict):
                    edit.set_selected(issue_info)

            else:
                edit = QLineEdit()
                edit.setMinimumHeight(36)
                edit.setFixedWidth(600)
                edit.setStyleSheet("""
                    QLineEdit {
                        background-color: rgb(179, 195, 208);
                        border: none;
                        border-radius: 5px;
                        padding-left: 10px;
                        color: rgb(27, 71, 93);
                        font-size: 14px;
                    }
                """)
                if col in self.values and self.values[col] is not None:
                    edit.setText(str(self.values[col]))

                if self.table_name == "books":
                    if col == "ISBN":
                        edit.setPlaceholderText("Например: 978-5-17-115234-5")
                        edit.setMaxLength(20)
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[\dX\-]+")))

                    elif col == "Название":
                        edit.setMaxLength(100)

                    elif col == "ББК":
                        edit.setPlaceholderText("Например: 84(2Рос=Рус)1")
                        edit.setMaxLength(20)
                        edit.setValidator(
                            QRegularExpressionValidator(QRegularExpression(r"[0-9А-Яа-яA-Za-z\(\)\=\-]+")))

                    elif col == "Жанр":
                        edit.setMaxLength(45)
                        edit.setValidator(
                            QRegularExpressionValidator(QRegularExpression(r"[0-9А-Яа-яA-Za-z\s\(\)\-\.]+")))

                    elif col == "Возраст":
                        edit.setPlaceholderText("Например: 6+")
                        edit.setMaxLength(10)
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{1,2}\+$")))

                    elif col == "Год издания":
                        edit.setPlaceholderText("Например: 2025")
                        edit.setMaxLength(4)
                        edit.setValidator(QIntValidator(1000, 3000))

                    elif col == "Количество":
                        edit.setMaxLength(5)
                        edit.setValidator(PositiveIntValidator())
                        edit.setPlaceholderText("От 1 до 99999")

                elif self.table_name == "librarians":
                    if col == "Логин":
                        edit.setPlaceholderText("Логин (без пробелов)")
                        edit.setMaxLength(50)
                        edit.setValidator(
                            QRegularExpressionValidator(QRegularExpression(r"[\w\-\.]+")))

                    elif col == "Пароль":
                        edit.setPlaceholderText("Пароль (минимум 4 символа)")
                        edit.setMaxLength(50)

                    elif col == "Фамилия":
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яA-Za-z\-]{2,50}$")))
                        edit.setMaxLength(50)

                    elif col == "Имя":
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яA-Za-z\-]{2,50}$")))
                        edit.setMaxLength(50)

                    elif col == "Отчество":
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яA-Za-z\-]{2,50}$")))
                        edit.setMaxLength(50)

                elif self.table_name == "readers":
                    if col == "Контакт родителя":
                        edit.setPlaceholderText("Например: 89574637389 или +7 (900) 123-45-67")
                        edit.setMaxLength(18)
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[\d\+\s\(\)\-]+")))

                    elif col == "Фамилия":
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яA-Za-z\-]{2,50}$")))
                        edit.setMaxLength(50)

                    elif col == "Имя":
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яA-Za-z\-]{2,50}$")))
                        edit.setMaxLength(50)

                    elif col == "Отчество":
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яA-Za-z\-]{2,50}$")))
                        edit.setMaxLength(50)

                    elif col == "Комментарий":
                        edit.setMaxLength(150)

                elif self.table_name == "hall":
                    if col == "Название":
                        edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[А-Яа-яA-Za-z\-]{2,50}$")))
                        edit.setMaxLength(50)

                    elif col == "Этаж":
                        edit.setMaxLength(5)
                        edit.setValidator(QIntValidator(1, 99999))

                elif self.table_name == "returns":
                    if col == "Комментарий":
                        edit.setMaxLength(150)

            self.inputs[col] = edit
            form_layout.addWidget(label)
            form_layout.addWidget(edit)
            form_layout.addWidget(error_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: rgb(248, 242, 239);
            }

            /* === ВЕРТИКАЛЬНЫЙ СКРОЛЛБАР === */
            QScrollBar:vertical {
                border: 1px solid rgb(179, 195, 208);
                background: rgb(240, 240, 240);
                width: 12px;
                border-radius: 5px;
                margin: 20px 0 20px 0;
            }
            QScrollBar::handle:vertical {
                background: #a0a0a0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #808080;
            }

            /* === ГОРИЗОНТАЛЬНЫЙ СКРОЛЛБАР (на случай если понадобится) === */
            QScrollBar:horizontal {
                border: 1px solid rgb(179, 195, 208);
                background: rgb(240, 240, 240);
                height: 12px;
                border-radius: 5px;
                margin: 0px 20px 0 20px;
            }
            QScrollBar::handle:horizontal {
                background: #a0a0a0;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #808080;
            }

            /* Убираем стрелки */
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
            }
        """)
        main_layout.addWidget(scroll)

        buttons_layout = QHBoxLayout()
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
                    border-radius: 10px;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: rgb(200, 210, 220); }
            """)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)
        main_layout.addLayout(buttons_layout)

        self.save_btn.clicked.connect(self.on_save)
        self.close_btn.clicked.connect(self.close)

    def on_save(self):
        for label in self.error_labels.values():
            label.hide()

        values = {}
        has_error = False

        try:
            for col, widget in self.inputs.items():
                if isinstance(widget, QDateEdit):
                    qdate = widget.date()
                    if qdate.isValid():
                        date_str = qdate.toString("yyyy-MM-dd")
                        values[col] = date_str
                    else:
                        values[col] = None

                elif isinstance(widget, QLineEdit):
                    text = widget.text().strip()
                    values[col] = text if text else None

                elif isinstance(widget, AuthorsSelector):
                    values[col] = widget.get_selected_ids()

                elif isinstance(widget, HallSelector):
                    values[col] = widget.get_selected_id()

                elif isinstance(widget, ReaderSelector):
                    values[col] = widget.get_selected_id()

                elif isinstance(widget, BookSelector):
                    values[col] = widget.get_selected_id()

                elif isinstance(widget, LibrarianSelector):
                    values[col] = widget.get_selected_id()

                elif isinstance(widget, IssueSelector):
                    values[col] = widget.get_selected_id()

                else:
                    raise TypeError(f"Неизвестный тип виджета: {type(widget)}")

                if col in self.required_fields:
                    value = values[col]
                    if value is None or \
                            (isinstance(value, list) and len(value) == 0) or \
                            (isinstance(value, str) and not value.strip()):
                        self.error_labels[col].setText("Заполните поле")
                        self.error_labels[col].show()
                        has_error = True

            if has_error:
                return

            issue_date = values.get("Дата выдачи")
            return_date = values.get("Дата возврата")

            if issue_date and return_date:
                from datetime import datetime
                issue_dt = datetime.strptime(issue_date, "%Y-%m-%d")
                return_dt = datetime.strptime(return_date, "%Y-%m-%d")

                if return_dt < issue_dt:
                    QMessageBox.warning(self, "Ошибка даты",
                                        "Дата возврата не может быть раньше даты выдачи")
                    return

            if self.table_name == "returns":
                issue_id = values.get("Выдача")
                return_date_str = values.get("Дата сдачи")

                if issue_id and return_date_str:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT ДатаВыдачи 
                            FROM issues 
                            WHERE id_выдачи = %s
                        """, (issue_id,))
                        row = cur.fetchone()
                        conn.close()

                        if row and row["ДатаВыдачи"]:
                            from datetime import datetime
                            issue_date_str = str(row["ДатаВыдачи"])
                            issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d")
                            return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

                            if return_date < issue_date:
                                QMessageBox.warning(
                                    self,
                                    "Ошибка даты",
                                    "Дата сдачи не может быть раньше даты выдачи"
                                )
                                return
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Ошибка",
                            f"Не удалось проверить дату выдачи:\n{e}"
                        )
                        return
            for col, widget in self.inputs.items():
                if isinstance(widget, (
                HallSelector, ReaderSelector, BookSelector, LibrarianSelector, IssueSelector, AuthorsSelector)):
                    value = values[col]
                    if value is None or (isinstance(value, list) and len(value) == 0):
                        QMessageBox.warning(self, "Ошибка", f"Выберите {col}")
                        return

            self.save_callback(values)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка сохранения", str(e))
            return

        if self.close_on_save:
            self.close()
        else:
            for widget in self.inputs.values():
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QDateEdit):
                    widget.setDate(QDate.currentDate())
                elif hasattr(widget, 'clear') and callable(getattr(widget, 'clear')):
                    try:
                        widget.clear()
                    except:
                        pass

class ConfirmDeleteDialog(QDialog):
    def __init__(self, confirm_callback):
        super().__init__()
        self.confirm_callback = confirm_callback
        self.setWindowTitle("Удаление записи")
        self.setFixedSize(400, 150)
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
                border-radius: 10px;
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

        message = QLabel("Вы действительно хотите удалить выбранную запись?")
        message.setWordWrap(True)
        layout.addWidget(message, alignment=Qt.AlignmentFlag.AlignCenter)

        buttons_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Да")
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