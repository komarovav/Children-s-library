import sys
from PyQt6.QtWidgets import QApplication
from windows import LoginWindow

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMessageBox {
            background-color: rgb(248, 242, 239);
        }
        QMessageBox QLabel {
            color: rgb(27, 71, 93);  /* цвет текста как везде */
            font-size: 14px;
        }
        QMessageBox QPushButton {
            background-color: rgb(179, 195, 208);
            border: none;
            color: rgb(27, 71, 93);
            border-radius: 10px;
            padding: 5px 15px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: rgb(200, 210, 220);
        }
    """)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
