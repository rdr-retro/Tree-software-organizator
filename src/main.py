import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from canvas_widget import Canvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Software Organization")
        self.canvas = Canvas()
        self.setCentralWidget(self.canvas)
        self.showMaximized()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
