import os
import sys
import time
import queue
import threading
import wave
import re
import numpy as np
import sounddevice as sd
import tkinter as tk
import winsound  # Thư viện phát âm thanh nội bộ của Windows
import sherpa_onnx
import ctranslate2
import transformers
from piper import PiperVoice

# ==========================================
# 0. CẤU HÌNH ĐƯỜNG DẪN AI 
# ==========================================
DIR_MODEL_VI = "./models/sherpa-onnx-zipformer-vi-int8-2025-04-20"
DIR_NLLB_CT2 = "./models/nllb-4way-finetuned-ct2" 
MODEL_NAME = "facebook/nllb-200-distilled-600M"
DIR_TTS_EN = "./models/en_US-lessac-low.onnx"

# ==========================================
# 1. KHỞI TẠO AI (Chạy một lần khi mở App)
# ==========================================
print("⏳ Đang nạp mô hình AI lên RAM... Vui lòng đợi!")

# Nạp ASR (Nghe tiếng Việt)
encoder_file = next((f for f in os.listdir(DIR_MODEL_VI) if f.startswith("encoder") and f.endswith(".onnx")), None)
decoder_file = next((f for f in os.listdir(DIR_MODEL_VI) if f.startswith("decoder") and f.endswith(".onnx")), None)
joiner_file = next((f for f in os.listdir(DIR_MODEL_VI) if f.startswith("joiner") and f.endswith(".onnx")), None)

model_vi = sherpa_onnx.OfflineRecognizer.from_transducer(
    tokens=f"{DIR_MODEL_VI}/tokens.txt",
    encoder=os.path.join(DIR_MODEL_VI, encoder_file),
    decoder=os.path.join(DIR_MODEL_VI, decoder_file),
    joiner=os.path.join(DIR_MODEL_VI, joiner_file),
    num_threads=2, sample_rate=16000, feature_dim=80
)

# Nạp NLLB (Dịch thuật)
translator = ctranslate2.Translator(DIR_NLLB_CT2, device="cpu", compute_type="int8")
tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)

# Nạp Piper TTS (Phát âm)
voice_en = PiperVoice.load(DIR_TTS_EN)

print("✅ Đã nạp AI thành công! Đang khởi động Giao diện...")

def clean_text_vi(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split()).capitalize()

def translate_vi_to_en(text):
    if not text.strip(): return ""
    tokenizer.src_lang = "vie_Latn"
    source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
    results = translator.translate_batch([source_tokens], target_prefix=[["eng_Latn"]])
    target_tokens = results[0].hypotheses[0][1:]
    return tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))


# ==========================================
# 2. THIẾT KẾ GIAO DIỆN APP (TKINTER GUI)
# ==========================================
class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Translator - Offline Desktop App")
        self.root.geometry("1000x600")
        self.root.configure(bg="#F0F4F8")
        
        # Các biến trạng thái luồng
        self.is_recording = False
        self.frames = []
        self.asr_stream = None
        self.last_text = ""
        self.output_audio_file = "output_en.wav" 
        
        # --- THIẾT KẾ UI ---
        title_lbl = tk.Label(root, text="HỆ THỐNG PHIÊN DỊCH REAL-TIME", 
                             font=("Segoe UI", 22, "bold"), bg="#F0F4F8", fg="#2C3E50")
        title_lbl.pack(side=tk.TOP, pady=20)
        
        # Nút bấm chính
        self.btn_record = tk.Button(root, text="🎙️ BẤM ĐỂ NÓI", font=("Segoe UI", 16, "bold"), 
                                    bg="#28A745", fg="white", activebackground="#218838", activeforeground="white",
                                    relief=tk.FLAT, cursor="hand2", command=self.toggle_recording)
        self.btn_record.pack(side=tk.BOTTOM, pady=20, ipadx=40, ipady=15)

        # Khung chứa 2 ô Text song song
        frame_text = tk.Frame(root, bg="#F0F4F8")
        frame_text.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        frame_text.columnconfigure(0, weight=1)
        frame_text.columnconfigure(1, weight=1)
        
        # Ô Tiếng Việt (Trái)
        lbl_vi = tk.Label(frame_text, text="🇻🇳 TIẾNG VIỆT", font=("Segoe UI", 12, "bold"), bg="#F0F4F8", fg="#0072B2")
        lbl_vi.grid(row=0, column=0, sticky="w", padx=10)
        
        self.txt_vi = tk.Text(frame_text, font=("Segoe UI", 16), wrap=tk.WORD, bg="#FFFFFF", 
                              fg="#333333", relief=tk.FLAT, padx=15, pady=15, height=8)
        self.txt_vi.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Ô Tiếng Anh + Nút Replay (Phải)
        frame_en_header = tk.Frame(frame_text, bg="#F0F4F8")
        frame_en_header.grid(row=0, column=1, sticky="w", padx=10)
        
        lbl_en = tk.Label(frame_en_header, text="🌍 TIẾNG ANH", font=("Segoe UI", 12, "bold"), bg="#F0F4F8", fg="#D55E00")
        lbl_en.pack(side=tk.LEFT)
        
        self.btn_replay = tk.Button(frame_en_header, text="🔊 Nghe lại", font=("Segoe UI", 10, "bold"),
                                    bg="#007BFF", fg="white", relief=tk.FLAT, cursor="hand2",
                                    state=tk.DISABLED, command=self.play_audio)
        self.btn_replay.pack(side=tk.LEFT, padx=15)
        
        self.txt_en = tk.Text(frame_text, font=("Segoe UI", 16), wrap=tk.WORD, bg="#FFF8F0", 
                              fg="#333333", relief=tk.FLAT, padx=15, pady=15, height=8)
        self.txt_en.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

    # --- LOGIC HOẠT ĐỘNG CHÍNH ---
    def audio_callback(self, indata, frames, time, status):
        """Hứng âm thanh liên tục từ Micro vào RAM"""
        if self.is_recording:
            self.frames.append(indata.copy().flatten())

    def toggle_recording(self):
        """Sự kiện chuyển đổi trạng thái Bật/Tắt Micro"""
        if not self.is_recording:
            # === BẮT ĐẦU NGHE ===
            self.is_recording = True
            self.btn_record.config(text="🔴 ĐANG NGHE... (BẤM ĐỂ DỪNG)", bg="#DC3545", activebackground="#C82333")
            self.btn_replay.config(state=tk.DISABLED) 
            
            # Xóa sạch dữ liệu cũ
            self.txt_vi.delete(1.0, tk.END)
            self.txt_en.delete(1.0, tk.END)
            self.last_text = ""
            self.frames = []
            self.asr_stream = model_vi.create_stream()
            
            # Kích hoạt luồng chạy âm thanh
            self.audio_thread = threading.Thread(target=self.process_audio, daemon=True)
            self.audio_thread.start()
            
        else:
            # === DỪNG NGHE VÀ XỬ LÝ ===
            self.is_recording = False
            self.btn_record.config(text="⏳ ĐANG XỬ LÝ AI...", bg="#FFC107", fg="black", state=tk.DISABLED)
            
            # Kích hoạt luồng Dịch & Phát âm (Để không làm đơ giao diện)
            threading.Thread(target=self.finish_translate_and_speak, daemon=True).start()

    def process_audio(self):
        """Luồng chuyên nhận diện tiếng Việt Real-time (Múa chữ)"""
        RATE = 16000
        with sd.InputStream(samplerate=RATE, channels=1, dtype='float32', callback=self.audio_callback):
            while self.is_recording:
                if len(self.frames) > 0:
                    current_audio = np.concatenate(self.frames, axis=0)
                    if len(current_audio) > RATE * 0.2:
                        # [SỬA LỖI LẶP CHỮ]: Luôn tạo stream ẢO MỚI TINH cho mỗi lần cập nhật múa chữ
                        temp_stream = model_vi.create_stream()
                        temp_stream.accept_waveform(RATE, current_audio)
                        model_vi.decode_stream(temp_stream)
                        
                        text = clean_text_vi(temp_stream.result.text)
                        if text != self.last_text and text.strip() != "":
                            self.update_ui_text(self.txt_vi, text + "...")
                            self.last_text = text
                time.sleep(0.15) 

    def finish_translate_and_speak(self):
        """Luồng chốt câu Tiếng Việt -> Dịch NLLB -> Phát Piper TTS"""
        RATE = 16000
        time.sleep(0.3) 
        
        if len(self.frames) == 0:
            self.update_ui_text(self.txt_vi, "(Không có âm thanh)")
            self.root.after(0, self.reset_button)
            return
            
        final_audio = np.concatenate(self.frames, axis=0)
        tail_silence = np.zeros(int(RATE * 0.5), dtype=np.float32)
        final_audio = np.concatenate((final_audio, tail_silence))
        
        # [SỬA LỖI LẶP CHỮ]: Sử dụng stream mới để chốt câu cuối cùng
        final_stream = model_vi.create_stream()
        final_stream.accept_waveform(RATE, final_audio)
        model_vi.decode_stream(final_stream)
        
        final_vi_text = clean_text_vi(final_stream.result.text)
        
        if final_vi_text.strip():
            self.update_ui_text(self.txt_vi, final_vi_text)
            
            final_en_text = translate_vi_to_en(final_vi_text)
            self.update_ui_text(self.txt_en, final_en_text)
            
            self.root.after(0, lambda: self.btn_record.config(text="🔊 ĐANG PHÁT ÂM...", bg="#17A2B8", fg="white"))
            with wave.open(self.output_audio_file, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(voice_en.config.sample_rate)
                voice_en.synthesize(final_en_text, wav_file)
            
            # Kích hoạt phát loa
            self.play_audio()
            
            self.root.after(0, lambda: self.btn_replay.config(state=tk.NORMAL))
            
        else:
            self.update_ui_text(self.txt_vi, "(Không nghe rõ, vui lòng thử lại)")
            
        self.root.after(0, self.reset_button)

    def play_audio(self):
        """Phát lại âm thanh đã chuẩn hóa sóng âm (Trị dứt điểm tiếng rè)"""
        if os.path.exists(self.output_audio_file):
            def _play_thread():
                try:
                    with wave.open(self.output_audio_file, 'rb') as wf:
                        framerate = wf.getframerate()
                        frames = wf.readframes(wf.getnframes())
                        
                        # 1. Đọc dữ liệu nguyên bản từ AI (Int16)
                        audio_data_int16 = np.frombuffer(frames, dtype=np.int16)
                        
                        # 2. CHUẨN HÓA SÓNG ÂM: Ép về số thực (Float32) và thu nhỏ dải sóng
                        audio_data_float32 = audio_data_int16.astype(np.float32) / 32768.0
                        
                        # 3. Phát ra loa với tín hiệu hoàn hảo
                        sd.play(audio_data_float32, samplerate=framerate)
                        sd.wait() 
                except Exception as e:
                    print(f"⚠️ Lỗi phát âm thanh: {e}")
            
            threading.Thread(target=_play_thread, daemon=True).start()

    def update_ui_text(self, text_widget, text):
        """Cập nhật giao diện an toàn từ luồng phụ"""
        def update():
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, text)
        self.root.after(0, update)
        
    def reset_button(self):
        """Khôi phục trạng thái nút bấm"""
        self.btn_record.config(text="🎙️ BẤM ĐỂ NÓI", bg="#28A745", fg="white", state=tk.NORMAL)

# ==========================================
# 3. KHỞI CHẠY
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()