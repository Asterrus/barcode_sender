import json
import subprocess
import tkinter as tk
from threading import Thread
from tkinter import messagebox, ttk
import re
import requests

devices = set()
devices_ip = set()
intent = 'android.intent.ACTION_DECODE_DATA'
variable = 'barcode_string'
WINDOW_WIDTH = 250
WINDOW_HEIGHT = 400
gs_symbol_input = '<GS>'
gs_symbol = chr(29)
barcode_settings_sending = False

def get_devices_ip():
    result = subprocess.run(['adb', 'shell', 'ip', 'addr', 'show', 'wlan0'],
                            stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    for ip in re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', output):
        devices_ip.add(ip)

    return devices_ip

get_devices_ip()

def find_devices():
    devices.clear()
    adb_command = 'adb devices'
    result = subprocess.run(adb_command, shell=True, capture_output=True, text=True)
    output = result.stdout
    lines = output.split('\n')
    for line in lines:
        if 'device' in line:
            device_name = line.split()[0]
            if device_name == 'List':
                continue
            devices.add(device_name)
    return devices

find_devices()

def refresh_devices():
    devices = list(find_devices())
    print("Устройства:", devices)
    if devices:
        selector.set(devices[0])
        selected_device_name.config(text=devices[0])
    else:
        selector.set('')
        selected_device_name.config(text='')
    ips = list(get_devices_ip())
    if ips:
        ip_selector.set(ips[0])
    else:
        ip_selector.set('')

def send_barcode():
    user_input = barc_label.get()
    print("Штрихкод:", user_input)
    if not user_input:
        error_label.config(text="Вы не ввели штрихкод")
        return
    device_name = selector.get()
    if not device_name:
        error_label.config(text="Устроство не выбрано")
        return
    error_label.config(text="")
    if gs_symbol_input in user_input:
        user_input = user_input.replace(gs_symbol_input, gs_symbol)
    print("user_input:", user_input)
    adb_command = f"adb -s {device_name} shell am broadcast -a {intent} --es {variable} {user_input}"
    subprocess.run(adb_command, shell=True)

def send_barcode_settings():
    global barcode_settings_sending
    if barcode_settings_sending:
        error_label.config(text="Настройки уже отправляются")
        return
    device_ip = ip_selector.get()
    if not device_ip:
        error_label.config(text="Устроство не выбрано")
        return
    barcode_settings_sending = True
    error_label.config(text="")
    params = {
        'mode': 'SyncCommand',
        'listener': 'set_config'
    }
    settings = {
        "rs_settings": {
            "logs_settings": {
                "enable_traceback": True
            },
        },
        'custom_settings': {
            'IntentScanner': True,
            'IntentScannerMessage': intent,
            'IntentScannerVariable': variable
        }
    }
    try:
        result = requests.post(f'http://{device_ip}:8095', params=params, json=settings)
        print(result.text)
    except Exception as e:
        print(e)
        error_label.config(text=str(e))
    root.event_generate("<<SendBarcodeSettingsTaskFinished>>", when="tail")

def send_barcode_settings_task_finished(event):
    global barcode_settings_sending
    barcode_settings_sending = False

def on_combobox_select(event):
    # Получаем выбранный элемент
    selected_item = selector.get()
    print("Выбран элемент:", selected_item)
    selected_device_name.config(text=selected_item)
    # Здесь может быть ваш код, который реагирует на выбор

root = tk.Tk()
root.title("Barcode Sender")
root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')


barc_label = tk.Label(root, text="Введите штрихкод или маркировку \n (Разделитель - <GS>):")
barc_label.pack()
barc_label = tk.Entry(root)
barc_label.pack()

intent_label = tk.Label(root, text="Введите intent:")
intent_label.pack()
intent_label = tk.Entry(root)
intent_label.insert(0, intent)
intent_label.config(state='disabled')
intent_label.pack()

variable_label = tk.Label(root, text="Введите variable:")
variable_label.pack()
variable_label = tk.Entry(root)
variable_label.insert(0, variable)
variable_label.config(state='disabled')
variable_label.pack()
devices_ip_options = list(devices_ip)
ip_selector_label = tk.Label(root, text="Выберите ip:")
ip_selector_label.pack()
ip_selector = ttk.Combobox(root, values=devices_ip_options)
ip_selector.bind('<<ComboboxSelected>>', on_combobox_select)
ip_selector.pack()
if devices_ip:
    ip_selector.set(devices_ip_options[0])
send_barcode_settings_button = tk.Button(root, text="Отправить настройки", command=lambda: Thread(target=send_barcode_settings).start())
send_barcode_settings_button.pack()
selected_device_label = tk.Label(root, text="Выбрано устройство:")
selected_device_label.pack()
selected_device_name = tk.Label(root, text="")
selected_device_name.pack()

submit_button = tk.Button(root, text="Обновить Устройства", command=refresh_devices)
submit_button.pack()
devices_options = list(devices)

selector_label = tk.Label(root, text="Выберите устройство:")
selector_label.pack()
selector = ttk.Combobox(root, values=devices_options)
selector.bind('<<ComboboxSelected>>', on_combobox_select)
print(devices_options)
if devices_options:
    selector.set(devices_options[0])
    selected_device_name.config(text=devices_options[0])

selector.pack()
submit_button = tk.Button(root, text="Отправить", command=send_barcode)
submit_button.pack()
error_label = tk.Label(root, text="")
error_label.pack()
root.bind("<<SendBarcodeSettingsTaskFinished>>", send_barcode_settings_task_finished)
root.mainloop()
