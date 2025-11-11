from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
import cv2
import time
import traceback
from ultralytics import YOLO
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class VideoThread(QThread):
    frame_ready = pyqtSignal(QImage)
    fps_ready = pyqtSignal(float)
    finished_signal = pyqtSignal()
    detection_info_ready = pyqtSignal(dict)

    def __init__(self, model_path, video_path, output_path, device='cpu', imgsz=640, save_video=False):
        super().__init__()

        if not os.path.isabs(model_path) and not model_path.startswith(('rtsp://', 'http://')):
            self.model_path = resource_path(model_path)
        else:
            self.model_path = model_path
        self.video_path = video_path
        self.output_path = os.path.join(os.path.expanduser("~"), "Road_Sign_Recognition_Result.avi")
        self.device = device
        self.imgsz = imgsz
        self.save_video = save_video

        self.model = YOLO(model_path)
        try:
            self.cap = cv2.VideoCapture(video_path)
        except Exception:
            self.cap = None

        self.is_paused = False
        self.running = True
        self.released = False
        self.out = None
        self.video_writer_initialized = False

    def run(self):
        try:
            if not self.cap or not self.cap.isOpened():
                print("[THREAD] Cannot open video file")
                return

            fps = self.cap.get(cv2.CAP_PROP_FPS)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            print(f"[DEBUG] Video source: {self.video_path}")
            print(f"[DEBUG] Video properties: {width}x{height}, FPS: {fps}")
            print(f"[DEBUG] Save video enabled: {self.save_video}")
            print(f"[DEBUG] Output path: {self.output_path}")

            frame_count = 0
            while self.running:
                if self.is_paused:
                    self.msleep(100)
                    continue

                ret, frame = self.cap.read()
                if not ret:
                    print("[THREAD] End of video or cannot read frame")
                    break

                frame_count += 1
                start_time = time.time()

                # Безопасный вызов predict
                try:
                    results = self.model.predict(frame, verbose=False, imgsz=self.imgsz, device=self.device)
                    annotated = results[0].plot()

                    detection_dict = self.extract_detection_info(results[0])
                    if detection_dict:
                        self.detection_info_ready.emit(detection_dict)

                    if self.save_video:
                        if not self.video_writer_initialized:
                            fourcc = cv2.VideoWriter_fourcc(*'XVID')
                            self.out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
                            if self.out.isOpened():
                                self.video_writer_initialized = True
                                print(f"[THREAD] Video recording STARTED: {self.output_path}")
                                print(f"[THREAD] Video writer initialized with: {width}x{height}, FPS: {fps}")
                            else:
                                print(f"[THREAD] FAILED to initialize video writer")
                                self.save_video = False

                        if self.video_writer_initialized and self.out.isOpened():
                            self.out.write(annotated)
                            if frame_count % 30 == 0:
                                print(f"[THREAD] Frame {frame_count} written to video")

                except Exception as e:
                    print(f"[THREAD] Prediction error: {e}")
                    traceback.print_exc()
                    break

                try:
                    rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    bytes_per_line = ch * w

                    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    self.frame_ready.emit(qimg.copy())
                except Exception as e:
                    print(f"[THREAD] Image conversion error: {e}")
                    continue

                end_time = time.time()
                fps_now = 1.0 / (end_time - start_time + 1e-6)
                self.fps_ready.emit(fps_now)

        except Exception as e:
            print(f"[THREAD] Exception in run: {e}")
            with open("video_thread_error.log", "a", encoding="utf-8") as f:
                f.write("Exception in VideoThread.run:\n")
                traceback.print_exc(file=f)
        finally:
            self.release()
            try:
                self.finished_signal.emit()
            except Exception as e:
                print(f"[THREAD] Error emitting finished signal: {e}")

    def extract_detection_info(self, result):
        try:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                return {}

            detection_dict = {}

            for box in boxes:
                class_id = int(box.cls.item())
                confidence = box.conf.item()
                class_name = result.names[class_id]

                if class_name in detection_dict:
                    if confidence > detection_dict[class_name]:
                        detection_dict[class_name] = confidence
                else:
                    detection_dict[class_name] = confidence

            return detection_dict

        except Exception as e:
            print(f"Error extracting detection info: {e}")
            return {}

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def stop(self):
        self.running = False
        self.msleep(100)

    def set_save_video(self, save_video):
        old_setting = self.save_video
        self.save_video = save_video

        if save_video and not old_setting:
            self.video_writer_initialized = False
            print(f"[THREAD] Video saving ENABLED, will start recording next frame")
        elif not save_video and old_setting:
            if self.out:
                self.out.release()
                self.out = None
            self.video_writer_initialized = False
            print("[THREAD] ⚫ Video recording STOPPED")

    def release(self):
        if self.released:
            return
        self.released = True
        print("[THREAD] Releasing resources...")
        try:
            if self.cap:
                self.cap.release()
                print("[THREAD] Video capture released")
            if self.out:
                self.out.release()
                print("[THREAD] Video writer released and file saved")
        except Exception as e:
            print(f"[THREAD] Release error: {e}")
        print("[THREAD] All resources released")