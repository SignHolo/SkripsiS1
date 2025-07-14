import cv2
import torch
import numpy as np
from ultralytics import YOLO
import sys
import socket
import time

# === TCP CLIENT CONFIG ===
SERVER_IP = '172.33.20.108' # This PC IP address
PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"[TCP] Connecting to server at {SERVER_IP}:{PORT}...")
try:
    client_socket.connect((SERVER_IP, PORT))
    print("[TCP] Connected to server.")
except Exception as e:
    print(f"[TCP] Connection failed: {e}")
    exit(1)
client_socket.send(b"opencv\n")  # Identifies this client

# === YOLO + VIDEO SETUP ===
model = YOLO("yolo11n.pt")
video_url = "http://192.168.137.54:8080/stream.mjpeg?clientId=JxuVC2E0sM9ohGjU" # Vid Stream URL
cap = cv2.VideoCapture(video_url)

# === SORT Tracker ===
sys.path.append("sort")
from sort import Sort
tracker = Sort(max_age=50, min_hits=5, iou_threshold=0.2)

colors = {}
zone_states = {"A": {}, "B": {}, "C": {}, "D": {}, "E": {}, "F": {}}
lights = {zone: 0 for zone in zone_states}

zones = {
    "A":  [(440, 235), (370, 225), (413, 155), (476, 155)],  
    "B": [(791, 229), (885, 225), (844, 150), (754, 155)],  
    "C": [(391, 341), (299, 337), (366, 244), (436, 247)],
    "D": [(836, 326), (950, 322), (890, 234), (797, 247)],
    "E": [(310, 508), (189, 504), (294, 346), (383, 349)],
    "F": [(1064, 478), (905, 480), (839, 338), (957, 333)]
}

np.random.seed(42)
def get_color(id):
    if id not in colors:
        colors[id] = tuple(map(int, np.random.randint(0, 255, size=3)))
    return colors[id]

def normalize_zone(zone):
    x1, y1, x2, y2 = zone
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

def is_inside_zone(cx, cy, zone):
    if isinstance(zone, list):  # polygon
        pts = np.array(zone, np.int32)
        return cv2.pointPolygonTest(pts, (cx, cy), False) >= 0
    else:  # rectangle
        x1, y1, x2, y2 = normalize_zone(zone)
        return x1 <= cx <= x2 and y1 <= cy <= y2

# === MAIN LOOP ===
while cap.isOpened():
    ret, frame = cap.read()
    frame = cv2.resize(frame, (1170, 540))
    if not ret:
        print("[INFO] Rewinding video...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    results = model(frame)
    detections = [[*map(int, box.xyxy[0]), box.conf[0].item()]
                  for result in results 
                  for box in result.boxes
                  if int(box.cls[0].item()) == 0]  # Class 0: person

    detections_array = np.array(detections)
    if detections_array.size == 0:
        detections_array = np.empty((0, 5))

    tracked_objects = tracker.update(detections_array)
    current_time = time.time()
    detected_ids = set()

    for obj in tracked_objects:
        x1, y1, x2, y2, obj_id = map(int, obj)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        detected_ids.add(obj_id)

        color = get_color(obj_id)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"ID {obj_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        for zone_name, zone_rect in zones.items():
            zone_data = zone_states[zone_name]
            if is_inside_zone(cx, cy, zone_rect):
                if obj_id not in zone_data:
                    zone_data[obj_id] = {
                        "enter_time": current_time,
                        "exit_time": None,
                        "active": False
                    }
                    print(f"[DEBUG] ID {obj_id} entered zone {zone_name}")
                else:
                    zone_info = zone_data[obj_id]
                    if zone_info["exit_time"] is not None:
                        zone_info["enter_time"] = current_time
                        zone_info["exit_time"] = None
                        zone_info["active"] = False
                        print(f"[DEBUG] ID {obj_id} re-entered zone {zone_name}")

                    if not zone_info["active"] and (current_time - zone_info["enter_time"] >= 2):
                        zone_info["active"] = True
                        print(f"[ZONE ON] Zone {zone_name} set to 1 due to ID {obj_id}")
            else:
                if obj_id in zone_data and zone_data[obj_id]["exit_time"] is None:
                    zone_data[obj_id]["exit_time"] = current_time
                    print(f"[DEBUG] ID {obj_id} exited zone {zone_name}")

    # Clean up and update light status
    for zone_name, zone_data in zone_states.items():
        to_delete = []
        for obj_id, data in zone_data.items():
            if data["exit_time"] and current_time - data["exit_time"] >= 5:
                print(f"[ZONE OFF] Zone {zone_name} removing ID {obj_id}")
                to_delete.append(obj_id)
        for obj_id in to_delete:
            del zone_data[obj_id]

        # Light ON if any active person
        lights[zone_name] = int(any(obj["active"] for obj in zone_data.values()))

    # === Send zone data to TCP server ===
    try:
        message = " ".join([f"zone_{k.lower()}={v}" for k, v in lights.items()])
        client_socket.sendall(message.encode())
        print("[TCP] Sent:", message)
    except Exception as e:
        print(f"[TCP] Send failed: {e}")
        break

    # === Draw zones ===
    for i, (zone_name, rect) in enumerate(zones.items()):
        z_color = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255)][i]
        if isinstance(rect, list):  # draw polygon
            pts = np.array(rect, np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=z_color, thickness=2)
        else:
            x1, y1, x2, y2 = normalize_zone(rect)
            cv2.rectangle(frame, (x1, y1), (x2, y2), z_color, 2)

        cv2.putText(frame, f"{zone_name}: {lights[zone_name]}", (rect[0] + 5, rect[1] + 20) if not isinstance(rect, list) else (rect[0][0] + 5, rect[0][1] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, z_color, 2)

    cv2.imshow("406 Lab Telekomunikasi", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# === CLEANUP ===
cap.release()
cv2.destroyAllWindows()
client_socket.close()
print("[EXIT] Video stream and socket closed.")
