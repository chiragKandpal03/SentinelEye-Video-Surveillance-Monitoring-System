# AI Smart Surveillance System 

A local educational prototype using Python/OpenCV/YOLO, Java Spring Boot, and PostgreSQL.

## What works in this starter
- Webcam or recorded video input
- YOLO person detection
- Configurable rectangular restricted zone and intrusion alerts
- Python sends event records to Spring Boot REST API
- Spring Boot stores and lists events in PostgreSQL
- Web dashboard with event counts and event history
- Optional fire/smoke model hook (`models/fire_smoke.pt`)
- Optional consent-based face enrollment/recognition module using OpenCV LBPH

## Important limitations
- The default YOLO model detects common objects including people; it does NOT detect fire/smoke.
- Fire/smoke detection stays disabled unless you supply a compatible custom model trained with `fire` and `smoke` classes.
- Face recognition is optional, local-only, and intended only for people who knowingly consent to enrollment. It is not enabled in the main detector by default.
- This is a student prototype, not a life-safety system. False positives and missed detections are possible.
- Ultralytics licensing may require a different license for some commercial uses. Check current licensing before commercial deployment.

## Requirements
- Windows 10/11
- Python 3.10 or 3.11 recommended
- JDK 17+
- Maven 3.9+
- PostgreSQL 15+ (or a supported newer version) and pgAdmin
- VS Code with the Python and Extension Pack for Java extensions

## Folder layout
- `python-ai/` Python detector and optional face tools
- `spring-backend/` Java REST API, dashboard, and PostgreSQL persistence
- `models/` optional custom fire/smoke model goes here

## 1. Install tools and configure PostgreSQL
Install PostgreSQL for Windows from https://www.postgresql.org/download/windows/. During setup, remember the password you create for the PostgreSQL `postgres` administrator. Keep the default port `5432` unless you deliberately changed it. pgAdmin is usually included.

Open pgAdmin, connect to your local PostgreSQL server, select **Tools → Query Tool** while connected to the default `postgres` database, and execute:

```sql
CREATE USER surveillance_user WITH PASSWORD 'ChangeThisPassword123!';
CREATE DATABASE surveillance_db OWNER surveillance_user;
```

If you already created either item, do not run its `CREATE` statement again. Instead, use the existing database/user and update `spring-backend/src/main/resources/application.properties` to match your credentials. The example password is for local learning only; change it before any real deployment.

## 2. Start Spring Boot
Open a terminal in `spring-backend`:

```powershell
mvn spring-boot:run
```

Check `http://localhost:8080/api/health` and open `http://localhost:8080`.

The database tables are created automatically by JPA for this local demo (`ddl-auto=update`). The first Maven run downloads Java dependencies, so internet access is needed.

## 3. Set up Python
Open a second terminal:

```powershell
cd python-ai
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Run the detector
Webcam:
```powershell
python detector.py --source 0
```

Recorded video:
```powershell
python detector.py --source "C:\path\to\video.mp4"
```

On first run, the YOLO model weights download automatically, so internet access is needed once. Press `q` in the video window to stop. The detector posts intrusion events to the Java API. Use only footage you are authorized to process.

## 5. Test the REST API manually
PowerShell:
```powershell
Invoke-RestMethod http://localhost:8080/api/health
Invoke-RestMethod http://localhost:8080/api/events
```

## 6. Fire/smoke and weapon detection
The project includes optional Ultralytics `.pt` models in `models/`. The fire/smoke model detects `fire` and `smoke`; the weapon model detects `gun` and `knife`. Start webcam analysis with both models using:

```powershell
python detector.py --source 0 --fire-model "..\models\fire_smoke.pt" --weapon-model "..\models\weapons.pt"
```

The fire/smoke model is from [mfranzon/fire-smoke-yolov8](https://huggingface.co/mfranzon/fire-smoke-yolov8) (AGPL-3.0). The gun/knife model is from [cosgun99/gun-knife-yolo11n](https://huggingface.co/cosgun99/gun-knife-yolo11n) (MIT). See `models/README.txt` for attribution. The detector displays fire/smoke events and `WEAPON` events on the dashboard. These community models can produce false positives or miss objects; this prototype is not a substitute for certified fire alarms or real security systems.

For a single photo, provide its path as the source; the annotated image opens in a window and generated alerts are sent to the dashboard:

```powershell
python detector.py --source "C:\path\to\photo.jpg" --fire-model "..\models\fire_smoke.pt" --weapon-model "..\models\weapons.pt"
```

## 7. Optional face module (consent-based demo)
This uses OpenCV's LBPH face recognizer, available in `opencv-contrib-python`.
Enroll a consenting participant:
```powershell
python enroll_face.py --name "Demo Person"
```
Follow the prompts and press `s` to save samples, `q` to finish. Then test the separate module:
```powershell
python face_module.py
```
Enrollment data is stored in `python-ai/face_data/`. Do not enroll people without informed consent. Keep this folder private and delete it when no longer needed. This module is deliberately separate from the main detector.

## Recommended run order (three terminals)
1. **Terminal 1:** start PostgreSQL (normally its Windows service starts automatically).
2. **Terminal 2:** in VS Code, open `spring-backend` and run `mvn spring-boot:run`. Wait until Spring Boot reports that it started.
3. **Terminal 3:** open `python-ai`, create/activate the virtual environment, install `requirements.txt`, and run `python detector.py --source 0`.
4. Open `http://localhost:8080` in your browser. When a person enters the configured restricted rectangle, the Python detector sends an event to the API and the dashboard can show it.

**Important:** the dashboard is an event dashboard, not a live video player. The camera/video appears in the OpenCV window. The standard YOLO weights detect people but do not automatically detect fire or smoke. Face recognition is a separate optional demo and should only be used with informed consent.

## Common problems
- `mvn` not recognized: install Maven, reopen terminal, run `mvn -v`.
- `java` not recognized: install JDK 17+, configure PATH, run `java -version`.
- PostgreSQL connection refused: ensure the PostgreSQL service is running on port 5432 and the database/user/password match `application.properties`.
- Webcam fails: close Camera/Teams/Zoom; try `--source 1`.
- `No module named cv2`: activate `.venv` and install requirements in that environment.
- CPU is slow: reduce `--imgsz 416`, close other apps, or use a supported GPU setup.
- Browser dashboard has no video: the Python detector opens its own OpenCV window; dashboard displays events, not a browser-embedded live stream.
