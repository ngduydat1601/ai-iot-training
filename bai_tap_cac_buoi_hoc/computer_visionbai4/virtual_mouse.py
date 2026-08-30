import cv2
import mediapipe as mp
import pyautogui
import math

# Tắt tính năng tự động ngắt của pyautogui để di chuột mượt hơn
pyautogui.FAILSAFE = False

# Lấy kích thước độ phân giải màn hình laptop (VD: 1920x1080)
screen_w, screen_h = pyautogui.size()

# === API MỚI - MediaPipe >= 0.10 ===
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Kết nối 21 landmarks
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]
# Tắt độ trễ ngầm của PyAutoGUI giúp chuột phản hồi tức thì
pyautogui.PAUSE = 0
# Các biến dùng cho thuật toán làm mượt (Smoothing)
smoothening = 7  # Càng lớn chuột càng mượt nhưng sẽ trễ nhịp hơn một chút (khuyên dùng 5 - 7)
plocX, plocY = 0, 0  # Tọa độ chuột ở khung hình trước (Previous Location)
clocX, clocY = 0, 0  # Tọa độ chuột ở khung hình hiện tại (Current Location)

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
    base_options=BaseOptions(model_asset_path=r'D:\Project\ai-iot-training_baihoc\bai_tap_cac_buoi_hoc\computer_visionbai4\hand_landmarker.task'),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1, # Giảm xuống 1 bàn tay để điều khiển chuột không bị nhiễu
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)
# Ép OpenCV sử dụng độ phân giải tối đa (HD 720p) của camera laptop
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)

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

        # Vẽ landmarks và Xử lý chuột ảo nếu phát hiện thấy tay
        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                # 1. Vẽ tay lên màn hình
                draw_hand_landmarks(frame, hand_landmarks, w, h)
                
                # 2. XỬ LÝ CHUỘT ẢO
                # Lấy dữ liệu ngón trỏ (8), ngón cái (4) và NGÓN GIỮA (12)
                index_finger = hand_landmarks[8]
                thumb_finger = hand_landmarks[4]
                middle_finger = hand_landmarks[12]
                
                # Chuyển tọa độ từ ảo (0.0 -> 1.0) sang pixel camera
                ix, iy = int(index_finger.x * w), int(index_finger.y * h)
                tx, ty = int(thumb_finger.x * w), int(thumb_finger.y * h)
                mx, my = int(middle_finger.x * w), int(middle_finger.y * h) # Tọa độ ngón giữa
                
                # Làm nổi bật 3 đầu ngón tay để dễ phân biệt vai trò
                cv2.circle(frame, (mx, my), 10, (255, 0, 0), -1)   # Ngón GIỮA: Xanh dương (Dùng để di chuyển)
                cv2.circle(frame, (tx, ty), 10, (255, 0, 255), -1) # Ngón cái: Hồng
                cv2.circle(frame, (ix, iy), 10, (0, 255, 255), -1) # Ngón trỏ: Vàng
                
                # === TÍNH NĂNG 1: DI CHUYỂN CHUỘT (DÙNG NGÓN GIỮA) ===
                # 1. Tính tọa độ mục tiêu mà NGÓN GIỮA đang chỉ tới
                target_x = int(middle_finger.x * screen_w)
                target_y = int(middle_finger.y * screen_h)
                
                # 2. Áp dụng công thức làm mượt (Smoothing)
                clocX = plocX + (target_x - plocX) / smoothening
                clocY = plocY + (target_y - plocY) / smoothening
                
                # 3. Ra lệnh di chuyển chuột tới tọa độ đã được làm mượt
                pyautogui.moveTo(clocX, clocY)
                
                # 4. Cập nhật lại tọa độ cũ cho vòng lặp tiếp theo
                plocX, plocY = clocX, clocY
                
                # === TÍNH NĂNG 2: CLICK CHUỘT (CHẠM NGÓN CÁI VÀO NGÓN TRỎ) ===
                # Tính khoảng cách giữa ngón cái (tx, ty) và ngón TRỎ (ix, iy)
                distance = math.hypot(tx - ix, ty - iy)
                
                # Vẽ 1 đường thẳng nối ngón cái và ngón trỏ để quan sát độ chụm
                cv2.line(frame, (ix, iy), (tx, ty), (0, 255, 255), 2)
                
                # Nếu khoảng cách < 50 pixel (tức là 2 ngón đã chụm lại)
                if distance < 50:
                    cv2.circle(frame, (ix, iy), 15, (0, 0, 255), -1) # Báo hiệu click bằng màu đỏ
                    pyautogui.click()
                    pyautogui.sleep(0.2) # Dừng 0.2s để chống click đúp

        cv2.imshow('Virtual Mouse - Tasks API', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()