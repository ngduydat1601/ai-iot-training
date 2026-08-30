import cv2
import mediapipe as mp

# === API MỚI - MediaPipe >= 0.10 ===
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Kết nối 21 landmarks (thay thế HAND_CONNECTIONS cũ)
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]

def draw_hand_landmarks(frame, hand_landmarks, width, height):
    """Vẽ 21 điểm và đường kết nối lên frame"""
    points = []
    for lm in hand_landmarks:
        x, y = int(lm.x * width), int(lm.y * height)
        points.append((x, y))
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)  # Điểm xanh lá

    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (0, 0, 255), 2)  # Đường đỏ

# Khởi tạo HandLandmarker với model file
options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=r'D:\\Project\\ai-iot-training_baihoc\\bai_tap_cac_buoi_hoc\\computer_visionbai4\\hand_landmarker.task'),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

with HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Lật ảnh như gương
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Chuyển BGR -> RGB cho MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Nhận diện tay
        result = landmarker.detect(mp_image)

        # Vẽ landmarks nếu phát hiện thấy tay
        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                draw_hand_landmarks(frame, hand_landmarks, w, h)

        cv2.imshow('MediaPipe Hand Tracking', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()