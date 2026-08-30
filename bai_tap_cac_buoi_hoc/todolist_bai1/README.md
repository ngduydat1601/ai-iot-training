# To-Do List App

Đây là một ứng dụng To-Do List đơn giản được xây dựng bằng Python và Tkinter.

## Chức năng
- Thêm công việc mới
- Hiển thị danh sách công việc
- Đánh dấu công việc đã hoàn thành
- Xóa công việc
- Tự động lưu dữ liệu vào file JSON
- Khi mở lại chương trình, dữ liệu vẫn được giữ lại

## Cấu trúc thư mục
```text
btap/todolist_bai1/
├── main.py
├── ui.py
├── task_manager.py
├── storage.py
├── data/
│   └── tasks.json
└── README.md
```

## Vai trò từng file
- main.py: điểm bắt đầu chương trình, khởi tạo cửa sổ Tkinter
- ui.py: xây dựng giao diện và xử lý các nút bấm
- task_manager.py: quản lý danh sách công việc và logic nghiệp vụ
- storage.py: đọc/ghi dữ liệu vào file JSON
- data/tasks.json: lưu trữ dữ liệu công việc

## Cách chạy
1. Mở terminal ở thư mục project
2. Chạy lệnh:
```bash
python main.py
```

## Luồng hoạt động
1. Khi chương trình khởi động, main.py tạo cửa sổ Tkinter.
2. ui.py hiển thị giao diện và gọi TaskManager khi người dùng thao tác.
3. TaskManager cập nhật dữ liệu trong bộ nhớ.
4. Storage lưu dữ liệu vào file JSON để giữ lại sau khi đóng chương trình.
