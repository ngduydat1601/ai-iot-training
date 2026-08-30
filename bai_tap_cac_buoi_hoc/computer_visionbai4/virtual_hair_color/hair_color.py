# ============================================================
# FILE: hair_color.py
# Chức năng: Chứa các hàm xử lý màu tóc
# Tách ra file riêng để code main.py gọn hơn, dễ bảo trì hơn
# ============================================================

import cv2
import numpy as np


# ============================================================
# PHẦN 1: BẢNG MÀU TÓC
# ============================================================

# Định nghĩa tất cả màu tóc có thể chọn
# Màu theo chuẩn BGR (Blue-Green-Red) của OpenCV
# Ví dụ: (0, 0, 255) = không Blue, không Green, full Red = màu Đỏ
HAIR_COLORS = {
    '1': ('Do',    (131,   142,   172)),   # Đỏ
    '2': ('Vang',  (169,   162, 159)),   # Vàng
    '3': ('Xanh',  (255, 0,   0  )),   # Xanh dương
    '4': ('Tim',   (128, 0,   128)),   # Tím
    '5': ('Hong',  (203, 192, 255)),   # Hồng
    '6': ('Cam',   (0,   165, 255)),   # Cam
    '7': ('Den',   (30,  30,  30 )),   # Đen
    '8': ('Nau',   (19,  69,  139)),   # Nâu
}


def get_color_list():
    """
    Trả về danh sách màu để hiển thị menu cho người dùng.
    
    Returns:
        dict: Dictionary {phím: (tên, màu BGR)}
    """
    return HAIR_COLORS


def create_color_overlay(frame_shape, color_bgr):
    """
    Tạo một lớp màu đơn sắc cùng kích thước với frame.
    
    Tại sao cần hàm này?
    - Không thể tô màu trực tiếp lên ảnh gốc (sẽ mất dữ liệu gốc)
    - Cần tạo một "lớp màu" riêng, rồi blend với ảnh gốc
    
    Args:
        frame_shape: Tuple (height, width, channels) của frame gốc
        color_bgr:   Tuple (B, G, R) màu muốn tô
    
    Returns:
        numpy array: Mảng ảnh với toàn bộ pixel = color_bgr
    
    Ví dụ:
        frame_shape = (480, 640, 3)
        color_bgr   = (0, 0, 255)   ← màu đỏ
        → Trả về mảng 480x640 toàn màu đỏ
    """
    overlay = np.zeros(frame_shape, dtype=np.uint8)
    overlay[:] = color_bgr  # Gán toàn bộ pixel = màu chọn
    return overlay


import cv2
import numpy as np

def apply_hair_color(frame, mask, color_bgr, alpha):
    # 1. LÀM MỀM CHÂN TÓC (Feathering)
    # Dùng Gaussian Blur làm nhòe viền của mask. Số (25, 25) càng lớn viền càng mềm
    blurred_mask = cv2.GaussianBlur(mask, (25,25), 0)
    
    # Quy đổi mask từ (0-255) về dải (0.0 -> 1.0) để làm hệ số nhân
    mask_weight = blurred_mask.astype(float) / 255.0
    mask_weight = np.dstack([mask_weight, mask_weight, mask_weight]) # Mở rộng ra 3 kênh màu

    # 2. GIỮ LẠI NẾP TÓC VÀ BÓNG TÓC
    # Tạo một bức ảnh tràn ngập màu bạn chọn
    color_overlay = np.full_like(frame, color_bgr, dtype=np.uint8)
    
    # Dùng addWeighted để trộn sáng/tối của ảnh gốc với lớp màu mới
    tinted_frame = cv2.addWeighted(frame, 1.0 - alpha, color_overlay, alpha, 0)

    # 3. GHÉP TÓC VÀO ẢNH CHÍNH
    # Chỗ nào là Tóc -> Lấy hình đã nhuộm. Chỗ nào là Nền -> Lấy ảnh gốc.
    result = (frame * (1 - mask_weight) + tinted_frame * mask_weight).astype(np.uint8)
    
    return result


def build_hair_mask(person_mask, face_mask):
    """
    Tính vùng tóc = Vùng người - Vùng mặt
    
    Giải thích phép toán:
    - person_mask: pixel trắng (255) = vùng người
    - face_mask  : pixel trắng (255) = vùng mặt
    - hair_mask  : pixel trắng (255) = vùng tóc (người nhưng không phải mặt)
    
    Dùng phép AND với NOT:
        hair = person AND (NOT face)
        = giữ lại pixel là người NHƯNG KHÔNG phải mặt
    
    Args:
        person_mask : Mask vùng người (từ Selfie Segmentation)
        face_mask   : Mask vùng mặt (từ Face Mesh)
    
    Returns:
        numpy array: Mask vùng tóc
    """
    # bitwise_not: đảo ngược mask (trắng↔đen)
    not_face = cv2.bitwise_not(face_mask)
    
    # bitwise_and: giữ pixel trắng chỉ khi CẢ HAI đều trắng
    hair_mask = cv2.bitwise_and(person_mask, not_face)
    
    return hair_mask


def get_person_mask(segmentation_result, threshold=0.5):
    """
    Chuyển kết quả Selfie Segmentation thành mặt nạ nhị phân.
    
    Selfie Segmentation trả về mảng float (0.0 đến 1.0):
    - Gần 1.0 = nhiều khả năng là người
    - Gần 0.0 = nhiều khả năng là nền
    
    Ta chọn ngưỡng (threshold) để phân loại:
    - Pixel > threshold → coi là người → gán = 255 (trắng)
    - Pixel ≤ threshold → coi là nền  → gán = 0   (đen)
    
    Args:
        segmentation_result : Kết quả từ mediapipe segmentation.process()
        threshold           : Ngưỡng phân loại (mặc định 0.5)
    
    Returns:
        numpy array: Mặt nạ nhị phân uint8 (0 hoặc 255)
    """
    mask_float = segmentation_result.segmentation_mask
    
    # So sánh: pixel > threshold → True → nhân 255 → 255
    #          pixel ≤ threshold → False → nhân 255 → 0
    binary_mask = (mask_float > threshold).astype(np.uint8) * 255
    
    return binary_mask