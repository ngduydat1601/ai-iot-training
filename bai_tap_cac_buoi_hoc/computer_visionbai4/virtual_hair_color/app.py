import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, render_template, Response, request
from hair_color import apply_hair_color

app = Flask(__name__)

current_color = (172, 142, 131) 
alpha = 0.3 # Độ trong suốt mặc định
# Từ điển ánh xạ phím số (1-6) thành mã màu BGR


# Khởi tạo MediaPipe Tasks API
BaseOptions = mp.tasks.BaseOptions
ImageSegmenter = mp.tasks.vision.ImageSegmenter
ImageSegmenterOptions = mp.tasks.vision.ImageSegmenterOptions
VisionRunningMode = mp.tasks.vision.RunningMode

seg_options = ImageSegmenterOptions(
    base_options=BaseOptions(model_asset_path='selfie_multiclass_256x256.tflite', delegate=BaseOptions.Delegate.CPU),
    running_mode=VisionRunningMode.IMAGE,
    output_category_mask=True,
    output_confidence_masks=False
)
segmenter = ImageSegmenter.create_from_options(seg_options)

def generate_frames():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Vẫn giữ tối ưu Buffer
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_count = 0
    last_hair_mask = None # Biến lưu lại vùng tóc của khung hình trước

    while True:
        success, frame = cap.read()
        if not success:
            break
            
        frame = cv2.flip(frame, 1)
        frame_count += 1
        
        # CHỈ CHẠY AI MỖI 2 KHUNG HÌNH (Khung số lẻ)
        if frame_count % 2 != 0 or last_hair_mask is None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            seg_result = segmenter.segment(mp_image)
            category_mask = seg_result.category_mask.numpy_view()
            
            # Tạo mask mới
            hair_mask = (category_mask == 1).astype(np.uint8) * 255
            if hair_mask.shape[:2] != frame.shape[:2]:
                hair_mask = cv2.resize(hair_mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
            
            # Lưu lại để khung hình sau dùng ké
            last_hair_mask = hair_mask

        # Áp màu tóc (luôn chạy, nhưng sử dụng mask mới hoặc mask xài ké)
        result = apply_hair_color(frame, last_hair_mask, current_color, alpha)

        # Nén ảnh (chất lượng 70%) để truyền web nhanh hơn
        ret, buffer = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    """Trang chủ hiển thị giao diện HTML"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Đường dẫn cung cấp luồng video"""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/set_custom_color', methods=['POST'])
def set_custom_color():
    """API nhận thông số pha màu tùy chỉnh từ thanh trượt Web"""
    global current_color
    try:
        # Nhận 3 thông số B, G, R từ giao diện
        b = int(request.form.get('b'))
        g = int(request.form.get('g'))
        r = int(request.form.get('r'))
        
        # Đảm bảo giá trị luôn nằm trong giới hạn màu 0-255
        if 0 <= b <= 255 and 0 <= g <= 255 and 0 <= r <= 255:
            current_color = (b, g, r) # OpenCV dùng BGR
            return "OK", 200
    except Exception as e:
        pass
        
    return "Invalid", 400
if __name__ == '__main__':
    # Chạy Web Server ở port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)