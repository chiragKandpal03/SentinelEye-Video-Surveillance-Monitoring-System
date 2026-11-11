import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import requests
from ultralytics import YOLO

API_EVENTS = "http://localhost:8080/api/events"
DEFAULT_MODEL = "yolo26n.pt"

def post_event(event_type, description, confidence=None, snapshot_path=None):
    payload = {
        "eventType": event_type,
        "description": description,
        "confidence": round(float(confidence), 4) if confidence is not None else None,
        "snapshotPath": snapshot_path,
        "source": "python-ai",
        "occurredAt": datetime.now(timezone.utc).isoformat()
    }
    try:
        response = requests.post(API_EVENTS, json=payload, timeout=2)
        response.raise_for_status()
        print(f"[ALERT] {event_type}: {description}")
    except requests.RequestException as exc:
        print(f"[WARN] Could not send event to Spring Boot ({exc}). Is the backend running?")

def main():
    parser = argparse.ArgumentParser(description="AI Smart Surveillance - person detection and intrusion alerts")
    parser.add_argument("--source", default="0", help="0 for webcam, or path to a video or image file")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="YOLO model weights")
    parser.add_argument("--fire-model", default="", help="Optional custom fire/smoke model path")
    parser.add_argument("--weapon-model", default="", help="Optional custom weapon model path (all model classes trigger an alert)")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--confidence", type=float, default=0.35)
    parser.add_argument("--cooldown", type=float, default=10.0, help="Seconds between repeated alerts of same type")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    model = YOLO(args.model)
    fire_model = None
    if args.fire_model:
        if Path(args.fire_model).exists():
            fire_model = YOLO(args.fire_model)
            print("[INFO] Fire/smoke model loaded. Verify its class names before use.")
        else:
            print(f"[WARN] Fire model path not found: {args.fire_model}; fire/smoke disabled.")
    weapon_model = None
    if args.weapon_model:
        if Path(args.weapon_model).exists():
            weapon_model = YOLO(args.weapon_model)
            print("[INFO] Weapon model loaded. Verify its class names and accuracy before use.")
        else:
            print(f"[WARN] Weapon model path not found: {args.weapon_model}; weapon detection disabled.")

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
    image_path = Path(args.source) if not args.source.isdigit() and Path(args.source).suffix.lower() in image_extensions else None
    image_frame = cv2.imread(str(image_path)) if image_path is not None else None
    if image_path is not None and image_frame is None:
        raise SystemExit(f"Could not read image: {image_path}")

    cap = None if image_path is not None else cv2.VideoCapture(source)
    if cap is not None and not cap.isOpened():
        raise SystemExit(f"Could not open video source: {source}. Try --source 1 or check the file path.")

    # Restricted zone is a rectangle covering the central-right portion of the frame.
    # Adjust these proportions for your own camera view.
    last_alert = {}
    last_status = 0
    if image_path is not None:
        print("Analyzing one image. Press any key in the image window to close it.")
    else:
        print("Press q in the video window to stop.")
    while True:
        if image_path is not None:
            ok, frame = True, image_frame.copy()
        else:
            ok, frame = cap.read()
        if not ok:
            break

        height, width = frame.shape[:2]
        zone_x1, zone_y1 = int(width * 0.55), int(height * 0.20)
        zone_x2, zone_y2 = int(width * 0.95), int(height * 0.90)
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 165, 255), 2)
        cv2.putText(frame, "RESTRICTED ZONE (edit in detector.py)", (zone_x1, max(22, zone_y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 2)

        result = model.predict(frame, imgsz=args.imgsz, conf=args.confidence, verbose=False)[0]
        people_inside = 0
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            class_name = str(model.names.get(class_id, class_id)).lower()
            if class_name != "person":
                continue
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            conf = float(box.conf[0].item())
            # Use the bottom-center of the box as an approximate ground-contact point.
            px, py = (x1 + x2) // 2, y2
            inside = zone_x1 <= px <= zone_x2 and zone_y1 <= py <= zone_y2
            color = (0, 0, 255) if inside else (0, 220, 0)
            label = f"person {conf:.2f}" + (" INTRUSION" if inside else "")
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (px, py), 4, color, -1)
            cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            if inside:
                people_inside += 1
                now = time.time()
                if now - last_alert.get("intrusion", 0) >= args.cooldown:
                    os.makedirs("snapshots", exist_ok=True)
                    snap = os.path.abspath(os.path.join("snapshots", f"intrusion_{int(now)}.jpg"))
                    cv2.imwrite(snap, frame)
                    post_event("INTRUSION", "Person detected in restricted zone", conf, snap)
                    last_alert["intrusion"] = now

        auxiliary_models = []
        if fire_model is not None:
            auxiliary_models.append((fire_model, "fire", ("fire", "smoke")))
        if weapon_model is not None:
            auxiliary_models.append((weapon_model, "weapon", None))

        for auxiliary_model, category, allowed_names in auxiliary_models:
            auxiliary_result = auxiliary_model.predict(
                frame, imgsz=args.imgsz, conf=args.confidence, verbose=False
            )[0]
            for box in auxiliary_result.boxes:
                class_id = int(box.cls[0].item())
                class_name = str(auxiliary_model.names.get(class_id, class_id)).lower()
                if allowed_names is not None and class_name not in allowed_names:
                    continue
                conf = float(box.conf[0].item())
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                color = (0, 0, 255) if category == "fire" else (255, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                now = time.time()
                key = f"{category}_{class_name}"
                if now - last_alert.get(key, 0) >= args.cooldown:
                    os.makedirs("snapshots", exist_ok=True)
                    snap = os.path.abspath(os.path.join("snapshots", f"{category}_{int(now)}.jpg"))
                    cv2.imwrite(snap, frame)
                    event_type = class_name.upper() if category == "fire" else "WEAPON"
                    post_event(event_type, f"Optional model detected {class_name}; verify manually", conf, snap)
                    last_alert[key] = now

        cv2.putText(frame, f"People in zone: {people_inside}", (12, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("AI Smart Surveillance - press q to quit", frame)
        if image_path is not None:
            cv2.waitKey(0)
            break
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        if time.time() - last_status > 30:
            print(f"[INFO] Detector running. Source={source}")
            last_status = time.time()

    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
