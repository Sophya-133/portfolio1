from datetime import datetime

class Task:
    def __init__(self, title, description="", category="", priority=3, deadline=None, status="not_done"):
        self.title = title
        self.description = description
        self.category = category
        if not (1 <= int(priority) <= 5):
            raise ValueError("Приоритет должен быть от 1 до 5.")
        self.priority = int(priority)
        self.deadline = deadline if deadline else None  
        self.status = status  

    def __repr__(self):
        status_str = "✅" if self.status == "done" else "❌"
        deadline_str = self.deadline.strftime("%Y-%m-%d") if self.deadline else "Нет срока"
        return f"[{status_str}] {self.title} | Категория: {self.category} | Приоритет: {self.priority} | Срок: {deadline_str}"

class TodoManager:
    def __init__(self):
        self.tasks = []

    def add_task(self):
        print("\nДобавление новой задачи:")
        title = input("Название задачи: ").strip()
        if not title:
            print("Название обязательно!")
            return
        description = input("Описание (по желанию): ").strip() or ""
        category = input("Категория: ").strip() or "Не указана"
        while True:
            try:
                priority = int(input("Приоритет (1-5): "))
                if 1 <= priority <= 5:
                    break
                else:
                    print("Приоритет должен быть от 1 до 5.")
            except ValueError:
                print("Введите число от 1 до 5.")
        deadline_input = input("Срок (формат YYYY-MM-DD, или пусто если нет): ").strip()
        deadline = None
        if deadline_input:
            try:
                deadline = datetime.strptime(deadline_input, "%Y-%m-%d")
            except ValueError:
                print("Неправильный формат даты. Будет установлен 'Нет срока'.")
                deadline = None
        status = "not_done"
        task = Task(title, description, category, priority, deadline, status)
        self.tasks.append(task)
        print("Задача добавлена.")

    def list_tasks(self, filter_category=None, sort_by="priority"):
        if not self.tasks:
            print("Список задач пуст.")
            return

        if filter_category:
            filtered = [t for t in self.tasks if t.category.lower() == filter_category.lower()]
            if not filtered:
                print(f"Нет задач в категории '{filter_category}'.")
                return
            tasks_to_show = filtered
        else:
            tasks_to_show = self.tasks

        if sort_by == "priority":
            tasks_to_show.sort(key=lambda t: t.priority)
        elif sort_by == "deadline":
            def deadline_key(t):
                return 0 if t.deadline is None else (t.deadline - datetime.now()).days
            tasks_to_show.sort(key=deadline_key)
        else:
            pass

        print("\nСписок задач:")
        for idx, task in enumerate(tasks_to_show, 1):
            print(f"{idx}. {task}")               

    def mark_done(self):
        self.list_tasks()
        if not self.tasks:
            return
        try:
            num = int(input("Введите номер задачи, которую хотите отметить как выполненную: ")) - 1
            if 0 <= num < len(self.tasks):
                self.tasks[num].status = "done"
                print("Задача отмечена как выполненная.")
            else:
                print("Некорректный номер задачи.")
        except ValueError:
            print("Введите число.")

    def delete_task(self):
        self.list_tasks()
        if not self.tasks:
            return
        try:
            num = int(input("Введите номер задачи для удаления: ")) - 1
            if 0 <= num < len(self.tasks):
                removed = self.tasks.pop(num)
                print(f"Задача '{removed.title}' удалена.")
            else:
                print("Некорректный номер задачи.")
        except ValueError:
            print("Введите число.")

    def show_by_category(self):
        categories = set(t.category for t in self.tasks)
        if not categories:
            print("Нет категорий.")
            return
        print("Доступные категории:")
        for idx, cat in enumerate(categories, 1):
            print(f"{idx}. {cat}")
        try:
            cat_choice = int(input("Выберите номер категории: ")) - 1
            cats_list = list(categories)
            if 0 <= cat_choice < len(cats_list):
                cat = cats_list[cat_choice]
                self.list_tasks(filter_category=cat)
            else:
                print("Некорректный номер категории.")
        except ValueError:
            print("Введите число.")


def main():
    todo = TodoManager()
    while True:
        print("\n--- TODO Manager ---")
        print("1. Добавить задачу")
        print("2. Показать все задачи")
        print("3. Отметить как выполненную")
        print("4. Удалить задачу")
        print("5. Показать задачи по категории")
        print("6. Выход")
        choice = input("Выберите действие: ")
        if choice == "1":
            todo.add_task()
        elif choice == "2":
            todo.list_tasks()
        elif choice == "3":
            todo.mark_done()
        elif choice == "4":
            todo.delete_task()
        elif choice == "5":
            todo.show_by_category()
        elif choice == "6":
            print("До свидания!")
            break
        else:
            print("Неверный выбор.")

if __name__ == "__main__":
    main()
