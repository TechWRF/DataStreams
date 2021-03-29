import sys
from PyQt5.QtWidgets import (
    QGridLayout,
    QApplication,
    QPushButton,
    QWidget,
    QTextEdit,
)
from PyQt5.QtGui import QFont
from PyQt5.QtTest import QTest

class Window(QWidget):
    def __init__(self, app, label_dict, controller_dict):
        super().__init__()
        self.setWindowTitle('Data Streams')
        self.label_dict = label_dict
        self.controller_dict = controller_dict
        
        app.aboutToQuit.connect(self.close_app)
        
        self.build_gui()
                
        self.update_freq = 1000
        
        self.controller_dict['app_running'] = True
        
    def close_app(self):
        self.controller_dict['app_running'] = False
        self.controller_dict['app_initialized'] = False
        
    def build_gui(self):
        grid_layout = QGridLayout()
        
        font = QFont('Arial', 14)

        x, y, i, j = 4, 6, 0, 0
        self.btn_dict = {}
        for hour in range(24):
            self.btn_dict[hour] = QPushButton(self.create_label(hour))
            self.btn_dict[hour].setFont(font)

            grid_layout.addWidget(self.btn_dict[hour], i, j)
            
            i += 1
            if i == y: i = 0 ; j += 1
        
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setFont(QFont('Arial', 10))
        
        start_btn = QPushButton('START')
        stop_btn = QPushButton('STOP')
        start_btn.clicked.connect(self.update_labels)
        stop_btn.clicked.connect(self.close_app)
        
        grid_layout.addWidget(self.text_box, 0, x, x, y-1)
        grid_layout.addWidget(start_btn, y-1, x, 1, 1)
        grid_layout.addWidget(stop_btn, y-1, x+1, 1, 1)
        self.setLayout(grid_layout)
                
    def create_label(self, hour):
        hour_label = '%d: [%d]' %(hour, self.label_dict[hour])
        if hour < 10: hour_label = '0%s' %hour_label
        return hour_label
    
    def update_labels(self):
        """
        Loop Updates Error Number and Log Box Each Second.
        Only User Can Start the Loop.
        """
        
        self.controller_dict['app_running'] = True
        while self.controller_dict['app_running']:
            for hour in range(24):                    
                self.btn_dict[hour].setText(self.create_label(hour))
            
            if len(self.controller_dict['log_text']) > 1:
                self.text_box.append(self.controller_dict['log_text'])
                self.controller_dict['log_text'] = ''
            
            QTest.qWait(self.update_freq)
                
if __name__ == '__main__':    
    label_dict = {h: 0 for h in range(24)}
    controller_dict = {}
    controller_dict['app_initialized'] = True
    controller_dict['app_running'] = False
    controller_dict['sleep_time'] = 1
    controller_dict['log_text'] = 'test'
    
    app = QApplication(sys.argv)
    window = Window(app, label_dict, controller_dict)
    window.show()
    app.exec_()