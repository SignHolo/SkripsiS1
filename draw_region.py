import cv2
import numpy as np

# === Video stream source ===
video_url = "http://192.168.137.54:8080/stream.mjpeg?clientId=JxuVC2E0sM9ohGjU"
cap = cv2.VideoCapture(video_url)

# === Global state ===
polygons = []
current_polygon = []
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
current_mouse_pos = (-1, -1)

def mouse_draw_polygon(event, x, y, flags, param):
    global current_polygon, polygons, current_mouse_pos
    current_mouse_pos = (x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))
    elif event == cv2.EVENT_RBUTTONDOWN and len(current_polygon) >= 3:
        polygons.append(current_polygon.copy())
        current_polygon.clear()

def draw_polygons(image, polygons, current_polygon, cursor_pos):
    img_copy = image.copy()

    for idx, poly in enumerate(polygons):
        color = colors[idx % len(colors)]
        pts = np.array(poly, np.int32)
        cv2.polylines(img_copy, [pts], isClosed=True, color=color, thickness=2)
        for pt in poly:
            cv2.circle(img_copy, pt, 5, color, -1)

    if current_polygon:
        for i in range(1, len(current_polygon)):
            cv2.line(img_copy, current_polygon[i-1], current_polygon[i], (128, 128, 128), 1)
            cv2.circle(img_copy, current_polygon[i-1], 5, (128, 128, 128), -1)
        cv2.line(img_copy, current_polygon[-1], cursor_pos, (180, 180, 180), 1)
        cv2.circle(img_copy, current_polygon[-1], 5, (128, 128, 128), -1)

    if cursor_pos != (-1, -1):
        cv2.circle(img_copy, cursor_pos, 4, (0, 0, 255), -1)

    return img_copy

def main():
    global current_mouse_pos

    if not cap.isOpened():
        print("[ERROR] Failed to open video stream.")
        return

    cv2.namedWindow("Image Window")
    cv2.setMouseCallback("Image Window", mouse_draw_polygon)

    print("Left click = add point | Right click = close polygon | Press 'q' to quit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame.")
            break

        frame = cv2.resize(frame, (1170, 540))
        display_img = draw_polygons(frame, polygons, current_polygon, current_mouse_pos)
        cv2.imshow("Image Window", display_img)

        key = cv2.waitKey(20) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("\nAll polygon coordinates:")
    for idx, poly in enumerate(polygons):
        print(f"Polygon {idx+1}: {poly}")

if __name__ == "__main__":
    main()
