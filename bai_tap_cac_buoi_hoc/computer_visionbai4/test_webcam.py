import cv2
import csv
from datetime import datetime
from ultralytics import YOLO

# Khởi tạo mô hình YOLOv8 (bản nano cho tốc độ nhanh nhất)
model = YOLO('yolov8n.pt')

# Mở kết nối Webcam
cap = cv2.VideoCapture(0)

# Mở file CSV để ghi log
with open('detections_log.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Ghi Header cho file CSV
    writer.writerow(['Timestamp', 'Class', 'Confidence', 'X1', 'Y1', 'X2', 'Y2'])

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Chạy YOLOv8 detect trên frame
        results = model.predict(frame, stream=True, verbose=False)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Trích xuất tọa độ, độ tự tin và nhãn
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = model.names[cls]

                # Vẽ bounding box và text lên frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{class_name} {conf:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Ghi log vào CSV
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                writer.writerow([timestamp, class_name, f"{conf:.2f}", x1, y1, x2, y2])

        # Hiển thị Webcam
        cv2.imshow('YOLOv8 Real-time Detection', frame)

        # Nhấn 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()