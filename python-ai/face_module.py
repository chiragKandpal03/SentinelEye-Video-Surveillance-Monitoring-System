from pathlib import Path
import cv2
import numpy as np

DATA = Path("face_data")
MODEL_FILE = DATA / "lbph_model.yml"
LABELS_FILE = DATA / "labels.json"

def train_model():
    if not hasattr(cv2, "face"):
        raise SystemExit("OpenCV face module missing. Install opencv-contrib-python in the active venv.")
    images, labels, label_map = [], [], {}
    next_id = 0
    for folder in sorted(DATA.iterdir()) if DATA.exists() else []:
        if not folder.is_dir():
            continue
        files = list(folder.glob("*.png"))
        if not files:
            continue
        label_map[str(next_id)] = folder.name
        for path in files:
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is not None:
                images.append(cv2.resize(image, (200, 200)))
                labels.append(next_id)
        next_id += 1
    if not images:
        raise SystemExit("No face samples found. Run enroll_face.py first.")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, np.array(labels, dtype=np.int32))
    recognizer.write(str(MODEL_FILE))
    LABELS_FILE.write_text(__import__("json").dumps(label_map, indent=2), encoding="utf-8")
    return recognizer, label_map

def main():
    import json
    if not DATA.exists():
        raise SystemExit("No face_data folder. Run enroll_face.py first.")
    recognizer, labels = train_model()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Cannot open webcam.")
    print("Local face demo. Press q to quit. Recognition can be wrong; do not use as proof of identity.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for (x, y, w, h) in detector.detectMultiScale(gray, 1.2, 5, minSize=(80, 80)):
            face = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
            label_id, distance = recognizer.predict(face)
            name = labels.get(str(label_id), "Unknown") if distance < 70 else "Unknown"
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 220, 0), 2)
            cv2.putText(frame, f"{name} (score {distance:.0f})", (x, max(20, y-8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 0), 2)
        cv2.imshow("Optional face demo - press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
