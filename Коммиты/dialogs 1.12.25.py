from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

class RecordDialog(QDialog):
    def __init__(self, columns: list[str], values: dict = None):
        super().__init__()
        self.setWindowTitle("Запись")
        self.inputs = {}
        layout = QVBoxLayout()
        for col in columns:
            h_layout = QHBoxLayout()
            label = QLabel(col)
            line_edit = QLineEdit()
            if values and col in values:
                line_edit.setText(str(values[col]))
            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)
            layout.addLayout(h_layout)
            self.inputs[col] = line_edit

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_values(self):
        return {col: self.inputs[col].text() for col in self.inputs}
