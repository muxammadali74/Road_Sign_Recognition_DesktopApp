import os

labels_dir = r"D:\Myprojects\Python\For_GitHub\Road_Sign_Recognition\TT100K-YOLO\labels\train"

classes = set()

for file_name in os.listdir(labels_dir):
    if file_name.endswith(".txt"):
        with open(os.path.join(labels_dir, file_name), "r") as f:
            for line in f:
                if line.strip():
                    cls_id = int(line.split()[0])
                    classes.add(cls_id)

print(f"Всего уникальных классов: {len(classes)}")
print(f"Список классов: {sorted(classes)}")
