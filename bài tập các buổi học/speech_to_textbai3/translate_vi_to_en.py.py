import os
import sys
import time
import queue
import threading
import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import font
import sherpa_onnx
import re
import ctranslate2
import transformers

# ==========================================
# 0. CẤU HÌNH ĐƯỜNG DẪN 
# ==========================================
DIR_MODEL_VI = "D:/Project/AIOT_training_khoahoc/python_code_begin/AI_translator/sherpa-onnx-zipformer-vi-int8-2025-04-20"
DIR_NLLB_CT2 = "./nllb-4way-finetuned-ct2" 
MODEL_NAME = "facebook/nllb-200-distilled-600M"

# ==========================================
# 1. BỘ CHUẨN HÓA VĂN BẢN
# ==========================================
def clean_text_vi(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split())

# ==========================================
# 2. KHỞI TẠO AI (Chạy trước khi mở App)
# ==========================================
print("⏳ Đang nạp mô hình vào RAM... Vui lòng đợi vài giây!")

# Nạp Sherpa-ONNX (Nhận diện giọng nói)
encoder_file = next((f for f in os.listdir(DIR_MODEL_VI) if f.startswith("encoder") and f.endswith(".onnx")), None)
decoder_file = next((f for f in os.listdir(DIR_MODEL_VI) if f.startswith("decoder") and f.endswith(".onnx")), None)
joiner_file = next((f for f in os.listdir(DIR_MODEL_VI) if f.startswith("joiner") and f.endswith(".onnx")), None)
        
model_vi = sherpa_onnx.OfflineRecognizer.from_transducer(
    tokens=f"{DIR_MODEL_VI}/tokens.txt",
    encoder=os.path.join(DIR_MODEL_VI, encoder_file),
    decoder=os.path.join(DIR_MODEL_VI, decoder_file),
    joiner=os.path.join(DIR_MODEL_VI, joiner_file),
    num_threads=2,
    sample_rate=16000,
    feature_dim=80
)

# Nạp NLLB Translator (Dịch thuật)
translator = ctranslate2.Translator(DIR_NLLB_CT2, device="cpu", compute_type="int8")
tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)
print("✅ Nạp AI thành công! Đang khởi động Giao diện...")

def translate_vi_to_en(text):
    if not text.strip(): return ""
    tokenizer.src_lang = "vie_Latn"
    source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
    results = translator.translate_batch([source_tokens], target_prefix=[["eng_Latn"]])
    target_tokens = results[0].hypotheses[0][1:]
    return tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))


# ==========================================
# 3. THIẾT KẾ GIAO DIỆN APP (GUI)
# ==========================================
class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Translator - Realtime")
        self.root.geometry("1000x600")
        self.root.configure(bg="#F0F4F8") # Màu nền sáng sủa, hiện đại
        
        # Biến trạng thái
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.asr_stream = None
        self.last_text = ""
        
        # --- THIẾT KẾ UI ---
        # 1. Tiêu đề
        title_lbl = tk.Label(root, text="HỆ THỐNG PHIÊN DỊCH vi sang en", 
                             font=("Segoe UI", 22, "bold"), bg="#F0F4F8", fg="#2C3E50")
        title_lbl.pack(side=tk.TOP, pady=20)
        
        # 2. Nút Điều khiển (Ghim cố định xuống đáy màn hình trước)
        self.btn_record = tk.Button(root, text="🎙️ BẤM ĐỂ NÓI", font=("Segoe UI", 16, "bold"), 
                                    bg="#59DC73", fg="white", activebackground="#218838", activeforeground="white",
                                    relief=tk.FLAT, cursor="hand2", command=self.toggle_recording)
        self.btn_record.pack(side=tk.BOTTOM, pady=20, ipadx=40, ipady=15)

        # 3. Khung chứa 2 ô Text song song (Sẽ tự động điền vào khoảng trống ở giữa)
        frame_text = tk.Frame(root, bg="#F0F4F8")
        frame_text.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
         
        frame_text.columnconfigure(0, weight=1)
        frame_text.columnconfigure(1, weight=1)
        
        # Ô Tiếng Việt (Bên Trái)
        lbl_vi = tk.Label(frame_text, text="TIẾNG VIỆT", font=("Segoe UI", 12, "bold"), bg="#F0F4F8", fg="#0072B2")
        lbl_vi.grid(row=0, column=0, sticky="w", padx=10)
        
        # Thêm height=8 để giới hạn chiều cao mặc định của khung text
        self.txt_vi = tk.Text(frame_text, font=("Segoe UI", 16), wrap=tk.WORD, bg="#FFFFFF", 
                              fg="#333333", relief=tk.FLAT, padx=15, pady=15, height=8)
        self.txt_vi.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Ô Tiếng Anh (Bên Phải)
        lbl_en = tk.Label(frame_text, text="TIẾNG ANH (Bản dịch)", font=("Segoe UI", 12, "bold"), bg="#F0F4F8", fg="#D55E00")
        lbl_en.grid(row=0, column=1, sticky="w", padx=10)
        
        self.txt_en = tk.Text(frame_text, font=("Segoe UI", 16), wrap=tk.WORD, bg="#FFF8F0", 
                              fg="#333333", relief=tk.FLAT, padx=15, pady=15, height=8)
        self.txt_en.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

   # --- LOGIC HOẠT ĐỘNG ---
    def audio_callback(self, indata, frames, time, status):
        """Hứng âm thanh liên tục và cất vào danh sách"""
        if self.is_recording:
            self.frames.append(indata.copy().flatten())

    def toggle_recording(self):
        """Xử lý sự kiện khi bấm nút"""
        if not self.is_recording:
            # === BẮT ĐẦU THU ÂM ===
            self.is_recording = True
            self.btn_record.config(text="🔴 ĐANG NGHE... (BẤM ĐỂ DỪNG)", bg="#DC3545", activebackground="#C82333")
            
            # Xóa chữ cũ và reset bộ nhớ âm thanh
            self.txt_vi.delete(1.0, tk.END)
            self.txt_en.delete(1.0, tk.END)
            self.last_text = ""
            self.frames = [] # Nơi chứa toàn bộ âm thanh của lần nói này
            
            # Khởi động luồng (Thread) chạy âm thanh
            self.audio_thread = threading.Thread(target=self.process_audio, daemon=True)
            self.audio_thread.start()
            
        else:
            # === DỪNG THU ÂM ===
            self.is_recording = False
            self.btn_record.config(text="⏳ ĐANG DỊCH...", bg="#FFC107", fg="black", state=tk.DISABLED)
            
            # Gọi luồng dịch thuật để chốt kết quả
            threading.Thread(target=self.finish_and_translate, daemon=True).start()

    def process_audio(self):
        """Luồng chuyên quét âm thanh và múa chữ Real-time"""
        RATE = 16000
        with sd.InputStream(samplerate=RATE, channels=1, dtype='float32', callback=self.audio_callback):
            while self.is_recording:
                if len(self.frames) > 0:
                    # Gom toàn bộ âm thanh từ lúc bấm nút đến hiện tại
                    current_audio = np.concatenate(self.frames, axis=0)
                    
                    # Chỉ giải mã khi âm thanh dài hơn 0.2s (TRỊ LỖI {1,80})
                    if len(current_audio) > RATE * 0.2:
                        stream = model_vi.create_stream()
                        stream.accept_waveform(RATE, current_audio)
                        model_vi.decode_stream(stream)
                        
                        text = clean_text_vi(stream.result.text)
                        
                        # Cập nhật giao diện nếu có chữ mới
                        if text != self.last_text and text.strip() != "":
                            self.update_ui_text(self.txt_vi, text.capitalize())
                            self.last_text = text
                            
                time.sleep(0.15) # Tốc độ chớp nhoáng 150ms/lần

    def finish_and_translate(self):
        """Chốt câu Tiếng Việt và ném sang NLLB để dịch"""
        RATE = 16000
        time.sleep(0.3) # Đợi nhịp thở cuối cùng
        
        if len(self.frames) == 0:
            self.update_ui_text(self.txt_vi, "(Không có âm thanh)")
            self.root.after(0, self.reset_button)
            return
            
        # Thêm 0.5s khoảng lặng ở đuôi để AI chốt từ cuối cùng chuẩn xác
        final_audio = np.concatenate(self.frames, axis=0)
        tail_silence = np.zeros(int(RATE * 0.5), dtype=np.float32)
        final_audio = np.concatenate((final_audio, tail_silence))
        
        stream = model_vi.create_stream()
        stream.accept_waveform(RATE, final_audio)
        model_vi.decode_stream(stream)
        
        final_vi_text = clean_text_vi(stream.result.text).capitalize()
        
        if final_vi_text.strip():
            self.update_ui_text(self.txt_vi, final_vi_text)
            
            # Đưa vào NLLB
            final_en_text = translate_vi_to_en(final_vi_text)
            self.update_ui_text(self.txt_en, final_en_text)
        else:
            self.update_ui_text(self.txt_vi, "(Không nghe rõ, vui lòng thử lại)")
            
        # Trả lại trạng thái ban đầu cho nút bấm
        self.root.after(0, self.reset_button)

    def update_ui_text(self, text_widget, text):
        """Hàm an toàn để cập nhật Giao diện từ một Luồng khác"""
        def update():
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, text)
        self.root.after(0, update)
        
    def reset_button(self):
        self.btn_record.config(text="🎙️ BẤM ĐỂ NÓI", bg="#28A745", fg="white", state=tk.NORMAL)
# ==========================================
# 4. KHỞI CHẠY ỨNG DỤNG
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()