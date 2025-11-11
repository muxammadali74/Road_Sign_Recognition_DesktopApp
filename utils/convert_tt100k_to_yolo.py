import os
import json
from PIL import Image

# пути
root = "data"
ann_path = os.path.join(root, "annotations.json")
img_dir = os.path.join(root, "train")
out_dir = "TT100K-YOLO"

# создаём папки
os.makedirs(os.path.join(out_dir, "images/train"), exist_ok=True)
os.makedirs(os.path.join(out_dir, "labels/train"), exist_ok=True)

# читаем json
data = json.load(open(ann_path))
imgs = data["imgs"]

# создаём список категорий
categories = sorted({obj["category"] for v in imgs.values() for obj in v.get("objects", [])})
cat2id = {c: i for i, c in enumerate(categories)}

for img_id, v in imgs.items():
    path = os.path.join(root, v["path"])
    if not os.path.exists(path):
        continue

    # открываем изображение для размера
    with Image.open(path) as im:
        w, h = im.size

    label_lines = []
    for obj in v.get("objects", []):
        bbox = obj["bbox"]
        x_center = (bbox["xmin"] + bbox["xmax"]) / 2 / w
        y_center = (bbox["ymin"] + bbox["ymax"]) / 2 / h
        bw = (bbox["xmax"] - bbox["xmin"]) / w
        bh = (bbox["ymax"] - bbox["ymin"]) / h
        cls_id = cat2id[obj["category"]]
        label_lines.append(f"{cls_id} {x_center} {y_center} {bw} {bh}")

    # сохраняем label
    if label_lines:
        base_name = os.path.basename(v["path"])
        img_out = os.path.join(out_dir, "images/train", base_name)
        lbl_out = os.path.join(out_dir, "labels/train", base_name.replace(".jpg", ".txt"))

        os.system(f'copy "{path}" "{img_out}"')
        with open(lbl_out, "w") as f:
            f.write("\n".join(label_lines))

print("✅ Конвертация завершена!")
