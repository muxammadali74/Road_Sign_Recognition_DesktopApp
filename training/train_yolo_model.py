from ultralytics import YOLO

def main():
    model = YOLO("../models/yolov8n.pt")
    model.train(
        data="dataset/data.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        device=0,
        workers=0
    )

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # 👈 важно для Windows
    main()
