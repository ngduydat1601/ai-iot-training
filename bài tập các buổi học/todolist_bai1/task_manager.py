from storage import load_tasks, save_tasks


class TaskManager:
    def __init__(self):
        self.tasks = self.load_tasks()

    def load_tasks(self):
        return load_tasks()

    def get_tasks(self):
        return self.tasks

    def add_task(self, title):
        clean_title = title.strip()
        if not clean_title:
            return False

        self.tasks.append({"title": clean_title, "completed": False})
        save_tasks(self.tasks)
        return True

    def toggle_task(self, index):
        if 0 <= index < len(self.tasks):
            self.tasks[index]["completed"] = not self.tasks[index]["completed"]
            save_tasks(self.tasks)
            return True
        return False

    def delete_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            save_tasks(self.tasks)
            return True
        return False
