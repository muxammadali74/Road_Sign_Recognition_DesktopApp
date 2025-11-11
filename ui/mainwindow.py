import sys
import traceback

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QVBoxLayout, QHBoxLayout, \
    QLabel, QLineEdit, QPushButton, QMessageBox
import os
from ui.Ui_MainWindow import Ui_MainWindow
from utils.logging_config import logger
from utils.video_thread import VideoThread
import torch


class RTSPDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RTSP Stream")
        self.setFixedSize(400, 120)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Input RTSP Link:")
        self.label.setStyleSheet("color: white; font: 10pt 'Roboto';")
        layout.addWidget(self.label)

        self.rtsp_input = QLineEdit()
        self.rtsp_input.setPlaceholderText("rtsp://username:password@ip:port/stream")
        self.rtsp_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: white;
                font: 9pt 'Roboto';
            }
        """)
        layout.addWidget(self.rtsp_input)

        button_layout = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font: 9pt 'Roboto';
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font: 9pt 'Roboto';
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_rtsp_link(self):
        return self.rtsp_input.text().strip()



class MainApp(QtWidgets.QMainWindow):
    @staticmethod
    def resource_path(relative_path):
        """Получает правильный путь для ресурсов при работе из EXE"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


    def __init__(self):
        try:
            logger.info("Initializing MainApp...")
            super().__init__()
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)

            self.thread = None
            self.model_path = self.resource_path("models/best.pt")
            self.video_path = None
            self.save_video = False

            self.ui.label_11.setText('Yolov8s')
            self.ui.label_12.setText(os.path.basename(self.model_path))
            if torch.cuda.is_available():
                self.ui.label_13.setText("CUDA GPU")
            else:
                self.ui.label_13.setText("CPU")

            self.detected_classes = {}

            self.ui.pushButton_5.clicked.connect(self.start_video)  # start
            self.ui.pushButton_4.clicked.connect(self.pause_video)  # pause
            self.ui.pushButton_3.clicked.connect(self.stop_video)  # stop
            self.ui.pushButton.clicked.connect(self.open_video_dialog)  # choose file
            self.ui.pushButton_6.clicked.connect(self.open_rtsp_dialog)  # RTSP button
            self.ui.pushButton_7.clicked.connect(self.toggle_save_video)  # Toggle save video

            self._closing = False

            self.setup_detection_table()

            self.update_save_button_icon()

        except Exception as e:
            logger.error(f"Error during MainApp initialization: {e}")
            logger.error(traceback.format_exc())
            raise

    def setup_detection_table(self):
        try:
            logger.debug("Setting up detection table")
            for i in reversed(range(self.ui.horizontalLayout.count())):
                self.ui.horizontalLayout.itemAt(i).widget().setParent(None)

            self.detection_table = QTableWidget()
            self.detection_table.setColumnCount(2)
            self.detection_table.setHorizontalHeaderLabels(["Class", "Accuracy"])

            self.detection_table.setStyleSheet("""
                QTableWidget {
                    background-color: #2b2b2b;
                    color: white;
                    border: none;
                    gridline-color: #3d3d3d;
                    font: 9pt "Roboto";
                }
                QTableWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #3d3d3d;
                }
                QHeaderView::section {
                    background-color: #1e1e1e;
                    color: white;
                    padding: 5px;
                    border: none;
                    font: 700 9pt "Roboto";
                }
            """)

            header = self.detection_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

            self.detection_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

            self.ui.horizontalLayout.addWidget(self.detection_table)
            logger.debug("Detection table setup completed")
        except Exception as e:
            logger.error(f"Error setting up detection table: {e}")


    def toggle_save_video(self):
        self.save_video = not self.save_video

        self.update_save_button_icon()

        if self.thread:
            self.thread.set_save_video(self.save_video)



    def update_save_button_icon(self):
        if self.save_video:
            icon = QtGui.QIcon(self.resource_path("ui/src/icons/record_off.png"))
            self.ui.pushButton_7.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.ui.pushButton_7.setToolTip("Сохранение видео ВКЛЮЧЕНО")
        else:
            icon = QtGui.QIcon(self.resource_path("ui/src/icons/record_off.png"))
            self.ui.pushButton_7.setStyleSheet("""
                QPushButton {
                    background-color: #666;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    background-color: #777;
                }
            """)
            self.ui.pushButton_7.setToolTip("Сохранение видео ВЫКЛЮЧЕНО")

        self.ui.pushButton_7.setIcon(icon)

    def open_video_dialog(self):
        file_filter = "Видео (*.mp4 *.MOV *.avi)"
        self.video_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите видео", "", file_filter)

        if self.video_path:
            self.update_source_status(os.path.basename(self.video_path))

    def open_rtsp_dialog(self):
        try:
            logger.info("Opening video file dialog")
            dialog = RTSPDialog(self)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    border: 1px solid #555;
                }
            """)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                rtsp_link = dialog.get_rtsp_link()
                if rtsp_link:
                    if not rtsp_link.startswith('rtsp://'):
                        QMessageBox.warning(self, "Invalid RTSP Link",
                                            "RTSP link should start with 'rtsp://'")
                        return

                    self.video_path = rtsp_link
                    self.update_source_status(
                        f"RTSP Stream: {rtsp_link[:50]}..." if len(rtsp_link) > 50 else f"RTSP Stream: {rtsp_link}")

        except Exception as e:
            logger.error(f"Error in open_video_dialog: {e}")

    def update_source_status(self, status_text):
        try:
            if hasattr(self.ui, 'label_15'):
                self.ui.label_15.setText(status_text)
            else:
                self.statusBar().showMessage(status_text)
        except Exception as e:
            print(f"Error updating source status: {e}")

    def start_video(self):
        try:
            logger.info("Attempting to start video processing")
            if not self.video_path:
                QMessageBox.warning(self, "No Source Selected",
                                    "Please select a video file or RTSP stream first.")
                return

            current_dir = os.path.dirname(os.path.abspath(__file__))
            result_dir = os.path.join(current_dir, "..", "result")
            os.makedirs(result_dir, exist_ok=True)

            output_path = os.path.join(result_dir, "result.avi")

            print(f"[APP] Absolute output path: {output_path}")

            self.detected_classes.clear()
            self.update_detection_table()

            if self.thread:
                self.thread.stop()
                self.thread.wait(2000)
                self.thread = None

            self.thread = VideoThread(
                self.model_path,
                self.video_path,
                output_path,
                device='cuda',
                imgsz=640,
                save_video=self.save_video
            )
            self.thread.frame_ready.connect(self.update_frame_from_qimage)
            self.thread.fps_ready.connect(self.update_fps)
            self.thread.finished_signal.connect(self.video_finished)
            self.thread.detection_info_ready.connect(self.update_detection_info)
            self.thread.start()

        except Exception as e:
            logger.error(f"Error in start_video: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to start video: {str(e)}")

    def handle_thread_error(self, error_message):
        """Обрабатывает ошибки из потока"""
        logger.error(f"Thread error: {error_message}")
        QMessageBox.critical(self, "Processing Error", error_message)

    def update_frame_from_qimage(self, qimg):
        try:
            qimg_copy = QtGui.QImage(qimg)
            pixmap = QtGui.QPixmap.fromImage(qimg_copy)
            scaled = pixmap.scaled(
                self.ui.label.width(), self.ui.label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.ui.label.setPixmap(scaled)
        except Exception as e:
            logger.error(f"Error in update_frame_from_qimage: {e}")

    def update_fps(self, fps):
            try:
                self.ui.label_5.setText(f"FPS: {fps:.1f}")
            except Exception:
                pass

    def update_detection_info(self, detections_dict):
        try:
            updated = False

            for class_name, confidence in detections_dict.items():
                if class_name in self.detected_classes:
                    if confidence > self.detected_classes[class_name]:
                        self.detected_classes[class_name] = confidence
                        updated = True
                else:
                    self.detected_classes[class_name] = confidence
                    updated = True

            if updated:
                self.update_detection_table()

        except Exception as e:
            print(f"Error updating detection info: {e}")

    def update_detection_table(self):
        try:
            sorted_classes = sorted(self.detected_classes.items(),
                                    key=lambda x: x[1], reverse=True)

            self.detection_table.setRowCount(len(sorted_classes))

            for row, (class_name, confidence) in enumerate(sorted_classes):
                class_item = QTableWidgetItem(class_name)
                class_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.detection_table.setItem(row, 0, class_item)

                accuracy_item = QTableWidgetItem(f"{confidence:.3f}")
                accuracy_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                if confidence > 0.8:
                    accuracy_item.setBackground(QtGui.QColor(0, 128, 0))
                elif confidence > 0.5:
                    accuracy_item.setBackground(QtGui.QColor(255, 165, 0))
                else:
                    accuracy_item.setBackground(QtGui.QColor(255, 0, 0))

                self.detection_table.setItem(row, 1, accuracy_item)

        except Exception as e:
            print(f"Error updating detection table: {e}")

    def pause_video(self):
        if self.thread:
            self.thread.toggle_pause()

    def stop_video(self):
        if self.thread:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(current_dir, "..", "result", "result.avi")

            self.thread.stop()
            self.thread.wait(2000)
            self.thread = None

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                file_size_mb = file_size / (1024 * 1024)
                print(f"[APP] Video file created: {output_path}")
                print(f"[APP] File size: {file_size_mb:.2f} MB")

            else:
                print(f"[APP] Video file NOT found: {output_path}")

            self.set_default_image()

    def video_finished(self):
        if self.thread:
            self.thread.wait(1000)
            self.thread = None
        self.set_default_image()
        try:
            self.ui.label_5.setText("FPS: 0.0")
        except Exception:
            pass

    def set_default_image(self):
        try:
            self.ui.label.clear()
            default_pixmap = QtGui.QPixmap(self.resource_path("ui/src/images/image.png"))
            if not default_pixmap.isNull():
                self.ui.label.setPixmap(default_pixmap)
        except Exception:
            pass

    def closeEvent(self, event):
        logger.info("Application closing...")
        self.safe_shutdown()
        event.accept()
        logger.info("Application closed")

    def safe_shutdown(self):
        """Полностью останавливает поток перед закрытием приложения"""
        logger.info("Safe shutdown started")
        if self.thread:
            try:
                logger.info("Stopping video thread")
                self.thread.stop()
                if not self.thread.wait(3000):
                    logger.warning("Thread didn't finish gracefully, terminating...")
                    self.thread.terminate()
                    self.thread.wait()
                logger.info("Video thread stopped")
            except Exception as e:
                logger.error(f"Error during thread shutdown: {e}")
            finally:
                self.thread = None
        logger.info("Safe shutdown completed")