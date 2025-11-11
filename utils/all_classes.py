import os
import cv2
import random
import matplotlib.pyplot as plt
from collections import defaultdict

# === Пути ===
labels_dir = '../TT100K-YOLO/labels'
images_dir = '../TT100K-YOLO/images'

# === Словарь: класс -> список (путь к изображению, bbox'ы) ===
class_to_images = defaultdict(list)

# === Собираем все label-файлы ===
for root, _, files in os.walk(labels_dir):
    for f in files:
        if f.endswith(".txt"):
            label_path = os.path.join(root, f)
            image_name = os.path.splitext(f)[0]

            # ищем соответствующее изображение
            possible_exts = ['.jpg', '.jpeg', '.png']
            image_path = None
            for ext in possible_exts:
                candidate = os.path.join(images_dir, os.path.relpath(root, labels_dir), image_name + ext)
                if os.path.exists(candidate):
                    image_path = candidate
                    break

            # читаем label
            if image_path:
                with open(label_path, "r") as lf:
                    lines = lf.readlines()
                for line in lines:
                    if line.strip():
                        class_id, x, y, w, h = map(float, line.split())
                        class_id = int(class_id)
                        # добавляем запись: (путь, [x,y,w,h])
                        class_to_images[class_id].append((image_path, [x, y, w, h]))

# === Визуализируем по 1 примеру для каждого класса ===
for cls_id, entries in sorted(class_to_images.items()):
    sample = random.choice(entries)
    image_path, bbox = sample
    img = cv2.imread(image_path)
    if img is None:
        continue

    h, w = img.shape[:2]
    x_center, y_center, bw, bh = bbox
    x1 = int((x_center - bw / 2) * w)
    y1 = int((y_center - bh / 2) * h)
    x2 = int((x_center + bw / 2) * w)
    y2 = int((y_center + bh / 2) * h)

    # рисуем рамку
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(img, f"Class {cls_id}", (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # показываем с помощью matplotlib (чтобы корректно отобразить цвета)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2.imwrite(f"../all_classes/{cls_id}.jpg", img)
