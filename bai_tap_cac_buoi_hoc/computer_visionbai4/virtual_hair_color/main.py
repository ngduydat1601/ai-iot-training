# ============================================================
# FILE: main.py  (Dùng selfie_multiclass - phân loại 6 vùng)
# Chạy: python main.py
# Yêu cầu file model cùng thư mục:
#   - selfie_multiclass_256x256.tflite
# ============================================================

import cv2
import mediapipe as mp
import numpy as np
import time

from hair_color import apply_hair_color
from ui_controls import (create_control_panel, read_trackbar_values,
                         update_control_panel, draw_info_overlay,
                         save_screenshot, reset_colors)


# ============================================================
# BƯỚC 1: Khai báo Tasks API
# ============================================================

BaseOptions           = mp.tasks.BaseOptions
ImageSegmenter        = mp.tasks.vision.ImageSegmenter
ImageSegmenterOptions = mp.tasks.vision.ImageSegmenterOptions
VisionRunningMode     = mp.tasks.vision.RunningMode


# ============================================================
# BƯỚC 2: Cấu hình model selfie_multiclass
# ============================================================
# Model này phân loại từng pixel thành 6 nhãn:
#   0 = nền, 1 = tóc, 2 = da thân, 3 = da mặt, 4 = quần áo, 5 = khác
# Dùng output_category_mask để lấy nhãn trực tiếp (không phải xác suất)

seg_options = ImageSegmenterOptions(
    base_options=BaseOptions(
        model_asset_path='selfie_multiclass_256x256.tflite'
    ),
    running_mode=VisionRunningMode.IMAGE,
    output_category_mask=True,       # Trả về nhãn (0,1,2,3,4,5) cho mỗi pixel
    output_confidence_masks=False
)


# ============================================================
# BƯỚC 3: Khởi tạo camera và UI
# ============================================================

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

create_control_panel()
prev_time = time.time()

print("=== VIRTUAL HAIR COLOR ===")
print("Keo thanh trong cua so 'Dieu Khien' de chon mau")
print("S: Luu anh | R: Reset mau | Q: Thoat")

# Nhãn TÓC trong model selfie_multiclass
HAIR_LABEL = 1


# ============================================================
# BƯỚC 4: Vòng lặp chính
# ============================================================

with ImageSegmenter.create_from_options(seg_options) as segmenter:

    while cap.isOpened():

        # 4.1 Đọc frame
        ret, frame = cap.read()
        if not ret:
            break

        # 4.2 Lật ảnh (gương)
        frame = cv2.flip(frame, 1)

        # 4.3 Đọc màu và độ đậm từ trackbar
        color_bgr, alpha = read_trackbar_values()

        # 4.4 Chuyển sang mp.Image (RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # ── SEGMENTATION ──────────────────────────────────────
        # 4.5 Chạy model phân loại vùng
        seg_result = segmenter.segment(mp_image)

        # category_mask: mảng 2D, mỗi pixel = nhãn (0..5)
        # numpy_view() trả về mảng uint8
        category_mask = seg_result.category_mask.numpy_view()

        # Lọc ra vùng TÓC: pixel nào có nhãn == 1 → 255, còn lại → 0
        hair_mask = (category_mask == HAIR_LABEL).astype(np.uint8) * 255

        # Resize mask về đúng kích thước frame gốc nếu khác nhau
        # (model 256x256 có thể trả mask nhỏ hơn frame)
        if hair_mask.shape[:2] != frame.shape[:2]:
            hair_mask = cv2.resize(
                hair_mask,
                (frame.shape[1], frame.shape[0]),
                interpolation=cv2.INTER_NEAREST
            )

        # ── ÁP MÀU TÓC ───────────────────────────────────────
        # 4.6 Blend màu tóc lên frame
        result = apply_hair_color(frame, hair_mask, color_bgr, alpha)

        # ── HIỂN THỊ ─────────────────────────────────────────
        # 4.7 Tính FPS
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time + 1e-9)
        prev_time = curr_time

        # 4.8 Vẽ thông tin và cập nhật UI
        result = draw_info_overlay(result, color_bgr, alpha, fps)
        update_control_panel(color_bgr, alpha)
        cv2.imshow("Virtual Hair Color", result)

        # ── PHÍM BẤM ─────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            save_screenshot(result)
        elif key == ord('r'):
            reset_colors()


# ============================================================
# BƯỚC 5: Dọn dẹp
# ============================================================
cap.release()
cv2.destroyAllWindows()
print("Da thoat.")