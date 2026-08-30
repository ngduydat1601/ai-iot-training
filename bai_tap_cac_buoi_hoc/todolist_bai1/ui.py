import tkinter as tk
from tkinter import messagebox

from task_manager import TaskManager


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List")
        self.root.geometry("420x480")
        self.root.resizable(False, False)

        self.task_manager = TaskManager()
        self.create_widgets()
        self.refresh_task_list()

    def create_widgets(self):
        title_label = tk.Label(
            self.root,
            text="Ứng dụng To-Do List",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(pady=(12, 8))

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill="x", padx=12, pady=6)

        self.task_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.task_entry.pack(side="left", fill="x", expand=True)
        self.task_entry.bind("<Return>", lambda event: self.add_task())

        add_button = tk.Button(input_frame, text="Thêm", width=8, command=self.add_task)
        add_button.pack(side="left", padx=(8, 0))

        self.task_listbox = tk.Listbox(
            self.root,
            height=15,
            font=("Arial", 11),
            selectmode=tk.SINGLE,
        )
        self.task_listbox.pack(fill="both", expand=True, padx=12, pady=8)

        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=12, pady=(0, 10))

        toggle_button = tk.Button(button_frame, text="Đánh dấu", command=self.toggle_selected_task)
        toggle_button.pack(side="left", expand=True, padx=(0, 4))

        delete_button = tk.Button(button_frame, text="Xóa", command=self.delete_selected_task)
        delete_button.pack(side="left", expand=True)

        self.status_label = tk.Label(self.root, text="Sẵn sàng", fg="gray", font=("Arial", 10))
        self.status_label.pack(pady=(0, 8))

    def add_task(self):
        task_title = self.task_entry.get()
        if self.task_manager.add_task(task_title):
            self.task_entry.delete(0, tk.END)
            self.refresh_task_list()
            self.status_label.config(text="Đã thêm công việc mới")
        else:
            messagebox.showwarning("Thông báo", "Vui lòng nhập tên công việc.")

    def toggle_selected_task(self):
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Thông báo", "Hãy chọn một công việc trước.")
            return

        index = selected_index[0]
        if self.task_manager.toggle_task(index):
            self.refresh_task_list()
            self.status_label.config(text="Đã cập nhật trạng thái")
        else:
            self.status_label.config(text="Không thể cập nhật")

    def delete_selected_task(self):
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Thông báo", "Hãy chọn một công việc trước.")
            return

        index = selected_index[0]
        if self.task_manager.delete_task(index):
            self.refresh_task_list()
            self.status_label.config(text="Đã xóa công việc")
        else:
            self.status_label.config(text="Không thể xóa")

    def refresh_task_list(self):
        self.task_listbox.delete(0, tk.END)
        tasks = self.task_manager.get_tasks()
        for task in tasks:
            prefix = "✓" if task.get("completed", False) else "○"
            self.task_listbox.insert(tk.END, f"{prefix} {task['title']}")
