import argparse
import json
from pathlib import Path
import cv2

def main():
    parser = argparse.ArgumentParser(description="Enroll a consenting participant for local face demo")
    parser.add_argument("--name", required=True, help="Participant name/label, with their informed consent")
    args = parser.parse_args()
    root = Path("face_data")
    root.mkdir(exist_ok=True)
    safe_name = "".join(c for c in args.name if c.isalnum() or c in ("_", "-")).strip()
    if not safe_name:
        raise SystemExit("Please provide a simple label.")
    person_dir = root / safe_name
    person_dir.mkdir(exist_ok=True)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Cannot open webcam.")
    count = len(list(person_dir.glob("*.png")))
    print("Look at the camera; press s to save a face sample, q to quit.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"Label: {safe_name} | samples: {count}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
        cv2.imshow("Face enrollment (consent required)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s") and len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            face = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
            cv2.imwrite(str(person_dir / f"{count:04d}.png"), face)
            count += 1
            print(f"Saved sample {count}")
    cap.release()
    cv2.destroyAllWindows()
    (root / "NOTICE.txt").write_text(
        "Contains face samples. Store securely, share only with consent, and delete when no longer needed.\n",
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
