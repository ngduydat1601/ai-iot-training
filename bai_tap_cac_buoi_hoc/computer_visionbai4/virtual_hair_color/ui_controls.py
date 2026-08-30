# ============================================================
# FILE: ui_controls.py
# Chức năng: Tạo giao diện người dùng (UI) với thanh trượt
#            để chọn màu tóc trực quan hơn dùng bàn phím
# ============================================================

import cv2
import numpy as np


# ============================================================
# PHẦN 1: HẰNG SỐ CỬA SỔ ĐIỀU KHIỂN
# ============================================================

CONTROL_WINDOW = "Dieu Khien Mau Toc"  # Tên cửa sổ trackbar
PREVIEW_WINDOW = "Virtual Hair Color"  # Tên cửa sổ hiển thị chính


# ============================================================
# PHẦN 2: TẠO CỬA SỔ TRACKBAR
# ============================================================

def create_control_panel():
    """
    Tạo cửa sổ điều khiển với các thanh trượt (trackbar).
    
    Tại sao dùng trackbar thay vì phím bấm?
    - Trực quan hơn: thấy ngay giá trị đang chọn
    - Dễ điều chỉnh: kéo thanh thay vì nhấn nhiều lần
    - Chọn được màu bất kỳ qua R, G, B riêng lẻ
    
    Các thanh trượt:
    1. R (Red)   : 0 → 255
    2. G (Green) : 0 → 255
    3. B (Blue)  : 0 → 255
    4. Alpha     : 0 → 100 (tương đương 0.0 → 1.0)
    
    Lưu ý: OpenCV dùng BGR không phải RGB,
    nhưng ta đặt tên R/G/B cho dễ hiểu với người dùng.
    """
    
    # Tạo cửa sổ trống (named window) để gắn trackbar vào
    cv2.namedWindow(CONTROL_WINDOW)
    
    # Tạo ảnh nền cho cửa sổ điều khiển (màu xám)
    # Nếu không có ảnh nền, trackbar sẽ không hiển thị đúng
    control_bg = np.ones((300, 400, 3), dtype=np.uint8) * 50  # Xám đậm
    cv2.imshow(CONTROL_WINDOW, control_bg)
    
    # Tạo trackbar cho từng kênh màu
    # cv2.createTrackbar(tên, cửa_sổ, giá_trị_mặc_định, giá_trị_max, callback)
    # callback: hàm gọi khi giá trị thay đổi (dùng lambda vì không cần làm gì)
    
    cv2.createTrackbar('Do (R)',        CONTROL_WINDOW, 0,   255, lambda x: None)
    cv2.createTrackbar('Xanh la (G)',   CONTROL_WINDOW, 0,   255, lambda x: None)
    cv2.createTrackbar('Xanh duong (B)',CONTROL_WINDOW, 255, 255, lambda x: None)
    cv2.createTrackbar('Do dam (%)',    CONTROL_WINDOW, 50,  100, lambda x: None)
    
    # Đặt màu mặc định là màu xanh dương (R=0, G=0, B=255)
    cv2.setTrackbarPos('Do (R)',         CONTROL_WINDOW, 0)
    cv2.setTrackbarPos('Xanh la (G)',    CONTROL_WINDOW, 0)
    cv2.setTrackbarPos('Xanh duong (B)', CONTROL_WINDOW, 255)
    cv2.setTrackbarPos('Do dam (%)',     CONTROL_WINDOW, 50)


def read_trackbar_values():
    """
    Đọc giá trị hiện tại từ các thanh trượt.
    
    Hàm này được gọi mỗi frame trong vòng lặp chính
    để lấy màu và độ đậm mà người dùng đang chọn.
    
    Returns:
        color_bgr : Tuple (B, G, R) màu hiện tại
        alpha     : Float 0.0-1.0 độ đậm hiện tại
    
    Ví dụ:
        Người dùng kéo R=255, G=0, B=0
        → color_bgr = (0, 0, 255)  ← nhớ OpenCV là BGR!
        → alpha = 0.5 (nếu thanh độ đậm ở 50%)
    """
    
    # Đọc giá trị từng trackbar
    r = cv2.getTrackbarPos('Do (R)',          CONTROL_WINDOW)
    g = cv2.getTrackbarPos('Xanh la (G)',     CONTROL_WINDOW)
    b = cv2.getTrackbarPos('Xanh duong (B)',  CONTROL_WINDOW)
    alpha_pct = cv2.getTrackbarPos('Do dam (%)', CONTROL_WINDOW)
    
    # Chuyển R,G,B sang BGR (OpenCV dùng BGR)
    color_bgr = (b, g, r)
    
    # Chuyển % sang float (50% → 0.5)
    alpha = alpha_pct / 100.0
    
    return color_bgr, alpha


# ============================================================
# PHẦN 3: CẬP NHẬT GIAO DIỆN
# ============================================================

def update_control_panel(color_bgr, alpha):
    """
    Vẽ bảng thông tin lên cửa sổ điều khiển.
    
    Hiển thị:
    - Ô màu preview (màu đang chọn)
    - Thông tin R, G, B
    - Độ đậm hiện tại
    - Hướng dẫn phím tắt
    
    Args:
        color_bgr : Tuple (B, G, R) màu hiện tại
        alpha     : Float độ đậm
    """
    
    # Tạo canvas (bảng vẽ) 300x400 pixel màu xám đậm
    panel = np.ones((300, 400, 3), dtype=np.uint8) * 40
    
    b, g, r = color_bgr  # Giải nén màu BGR
    
    # ----- Vẽ ô preview màu tóc -----
    # Hình chữ nhật màu đang chọn (để người dùng thấy ngay)
    cv2.rectangle(panel,
                  pt1=(10, 10),    # Góc trên trái (x, y)
                  pt2=(150, 80),   # Góc dưới phải (x, y)
                  color=color_bgr,
                  thickness=-1)    # -1 = tô đặc, dương = chỉ vẽ viền
    
    # Viền trắng quanh ô màu
    cv2.rectangle(panel, (10, 10), (150, 80), (255, 255, 255), 2)
    
    # Chữ "Mau chon" bên dưới ô màu
    cv2.putText(panel, "Mau chon:", (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    # ----- Hiển thị giá trị R, G, B -----
    cv2.putText(panel, f"R = {r}", (170, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 2)
    cv2.putText(panel, f"G = {g}", (170, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
    cv2.putText(panel, f"B = {b}", (170, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 2)
    
    # ----- Hiển thị thanh độ đậm -----
    cv2.putText(panel, f"Do dam: {int(alpha*100)}%", (10, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Vẽ thanh tiến trình (progress bar) cho độ đậm
    bar_width = int(380 * alpha)  # Chiều dài thanh theo %
    cv2.rectangle(panel, (10, 140), (390, 160), (80, 80, 80), -1)    # Nền xám
    cv2.rectangle(panel, (10, 140), (10 + bar_width, 160), (0, 200, 0), -1)  # Thanh xanh
    
    # ----- Hướng dẫn phím tắt -----
    instructions = [
        "Keo thanh tren de chon mau",
        "Phim S: Luu anh",
        "Phim R: Reset ve mac dinh",
        "Phim Q: Thoat",
    ]
    for i, text in enumerate(instructions):
        cv2.putText(panel, text, (10, 190 + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    
    # Cập nhật cửa sổ điều khiển
    cv2.imshow(CONTROL_WINDOW, panel)


# ============================================================
# PHẦN 4: CÁC HÀM TIỆN ÍCH
# ============================================================

def save_screenshot(frame, filename=None):
    """
    Lưu frame hiện tại thành file ảnh.
    
    Args:
        frame    : Frame cần lưu (numpy array)
        filename : Tên file (nếu None thì tự tạo tên theo thời gian)
    
    Returns:
        str: Đường dẫn file đã lưu
    """
    import datetime
    
    if filename is None:
        # Tạo tên file theo thời gian: hair_20240825_143000.jpg
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hair_{timestamp}.jpg"
    
    cv2.imwrite(filename, frame)
    print(f"[INFO] Da luu anh: {filename}")
    return filename


def reset_colors():
    """
    Đặt lại trackbar về màu mặc định (xanh dương, độ đậm 50%).
    """
    cv2.setTrackbarPos('Do (R)',          CONTROL_WINDOW, 0)
    cv2.setTrackbarPos('Xanh la (G)',     CONTROL_WINDOW, 0)
    cv2.setTrackbarPos('Xanh duong (B)',  CONTROL_WINDOW, 255)
    cv2.setTrackbarPos('Do dam (%)',      CONTROL_WINDOW, 50)
    print("[INFO] Da reset ve mau mac dinh")


def draw_info_overlay(frame, color_bgr, alpha, fps=0):
    """
    Vẽ thông tin lên góc trái của frame chính.
    
    Hiển thị:
    - FPS (tốc độ khung hình)
    - Màu đang chọn (R, G, B)
    - Độ đậm
    
    Args:
        frame     : Frame cần vẽ thông tin lên
        color_bgr : Màu hiện tại
        alpha     : Độ đậm
        fps       : Frames per second
    
    Returns:
        numpy array: Frame đã vẽ thông tin
    """
    b, g, r = color_bgr
    
    # Vẽ nền mờ cho text (dễ đọc hơn)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (280, 100), (0, 0, 0), -1)
    # addWeighted: blend overlay với frame gốc (tạo hiệu ứng trong suốt)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
    
    # Vẽ thông tin
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Mau: R={r} G={g} B={b}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, f"Do dam: {int(alpha*100)}%", (10, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, "S: Luu  R: Reset  Q: Thoat", (10, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    
    return frame