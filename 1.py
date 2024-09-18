import tkinter as tk
from threading import Thread
import time

def blocking_task():
    # Длительная задача
    print("Начало длительной операции")
    time.sleep(5)  # Имитация длительной операции
    print("Окончание длительной операции")
    # Важно: обновления интерфейса должны выполняться в основном потоке
    window.event_generate("<<TaskFinished>>", when="tail")

def on_task_finished(event):
    label.config(text="Операция завершена!")

window = tk.Tk()
window.title("Блокировка UI потока в Tkinter")

label = tk.Label(window, text="Нажмите кнопку для начала операции")
label.pack(pady=20)

button = tk.Button(window, text="Запустить длительную операцию", command=lambda: Thread(target=blocking_task).start())
button.pack(pady=20)

window.bind("<<TaskFinished>>", on_task_finished)

window.mainloop()