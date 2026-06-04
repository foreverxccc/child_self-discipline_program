from PySide6.QtCore import QUrl, QCoreApplication, QTimer
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
effect = QSoundEffect()
effect.setSource(QUrl.fromLocalFile(r"D:\pythonWork\child_self-discipline_program\app\assets\sounds\lingsheng.wav"))
effect.play()

def check_status():
    print(f"Status: {effect.status()}")
    if effect.status() == QSoundEffect.Error:
        print("Error playing sound")
    if not effect.isPlaying():
        QCoreApplication.quit()

timer = QTimer()
timer.timeout.connect(check_status)
timer.start(500)
QTimer.singleShot(5000, QCoreApplication.quit)
app.exec()
