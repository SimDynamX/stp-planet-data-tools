import sys
from PySide2.QtWidgets import (QApplication, QVBoxLayout, QWidget, QPushButton, 
                               QFileDialog, QListWidget, QDoubleSpinBox, QLineEdit, 
                               QCheckBox, QProgressBar, QLabel)


class AppGUI(QWidget):
    def __init__(self):
        super().__init__()

        # Layout
        layout = QVBoxLayout()

        # Widgets for inputFiles
        self.file_list = QListWidget()
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file)
        layout.addWidget(QLabel("Input Files:"))
        layout.addWidget(self.file_list)
        layout.addWidget(add_file_btn)

        # Widget for radius
        self.radius_input = QDoubleSpinBox()
        self.radius_input.setRange(0, 10000)  # Example range
        layout.addWidget(QLabel("Radius:"))
        layout.addWidget(self.radius_input)

        # Widgets for string inputs
        self.prjFileRoot_input = QLineEdit()
        self.prjFileSide_input = QLineEdit()
        layout.addWidget(QLabel("Prj File Root:"))
        layout.addWidget(self.prjFileRoot_input)
        layout.addWidget(QLabel("Prj File Side:"))
        layout.addWidget(self.prjFileSide_input)

        # Progress Bar
        self.progBar = QProgressBar()
        layout.addWidget(self.progBar)

        # Other parameters with default values (as example)
        self.mpp_input = QDoubleSpinBox()
        self.mpp_input.setRange(0, 1000)  # Example range
        layout.addWidget(QLabel("Meters per Pixel:"))
        layout.addWidget(self.mpp_input)

        self.forceFullSideExtents_chk = QCheckBox("Force Full Side Extents")
        layout.addWidget(self.forceFullSideExtents_chk)

        # Add more widgets as necessary...

        # Submit button
        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.submit)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def add_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_name:
            self.file_list.addItem(file_name)

    def submit(self):
        inputFiles = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        radius = self.radius_input.value()
        prjFileRoot = self.prjFileRoot_input.text()
        prjFileSide = self.prjFileSide_input.text()
        progBar = self.progBar
        meters_per_pixel = self.mpp_input.value()
        forceFullSideExtents = self.forceFullSideExtents_chk.isChecked()
        # Add more parameters as needed

        Gnomonic_Warp(
            inputFiles, radius, prjFileRoot, prjFileSide, progBar, 
            meters_per_pixel=meters_per_pixel, forceFullSideExtents=forceFullSideExtents
        )
        # Add more arguments as needed...

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppGUI()
    window.show()
    sys.exit(app.exec_())
