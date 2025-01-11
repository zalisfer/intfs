from tkinter import *
from tkinter import ttk, messagebox
import subprocess

class NetworkConfigurator:
    def __init__(self):
        root = Tk() 
        root.title("INTFS") 
        root.geometry("500x300+700+350")
        root.resizable(True, True)  
        root.attributes('-alpha', 1)
        
        self.interfaces = self.get_network_interfaces()
        self.interface_combobox = ttk.Combobox(values = self.interfaces)
        self.interface_combobox.pack(ipadx=40)
        self.interface_combobox.bind("<<ComboboxSelected>>", self.load_interface_config)

        frame_grid = ttk.Frame()
        frame_grid.pack()

        ttk.Label(master=frame_grid, text='ip').grid(row=1, column=1)
        self.ip_entry = ttk.Entry(master=frame_grid)
        self.ip_entry.grid(row=1, column=2, padx=10, pady=5)

        ttk.Label(master=frame_grid,text='netmask').grid(row=2, column=1)
        self.netmask_entry = ttk.Entry(master=frame_grid)
        self.netmask_entry.grid(row=2, column=2, padx=10,pady=5)

        ttk.Label(master=frame_grid, text='gateway').grid(row=3, column=1)
        self.gateway_entry = ttk.Entry(master=frame_grid)
        self.gateway_entry.grid(row=3, column=2, padx=10,pady=5)

        apply = Button(text='Apply Static Configuration', command=self.apply_static_config)
        apply.pack(pady=5)

        dhcp_button = Button(text="Set to DHCP", command=self.apply_dhcp_config)
        dhcp_button.pack(pady=5)

        root.mainloop() 

    # функция для получения названий сетевых интерфейсов
    def get_network_interfaces(self):
        try:
            result = subprocess.check_output(['ip', 'link'], encoding='utf-8')
            interfaces = []
            for line in result.splitlines():
                if ': ' in line:
                    name = line.split(': ')[1].split(':')[0]
                    if name != 'lo':  # Исключаем локальный интерфейс
                        interfaces.append(name)
            return interfaces
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve interfaces: {e}")
            return []

    #подтягивает данные из конфиг файла, если они там уже есть
    def load_interface_config(self, event):
        interface = self.interface_combobox.get()
        config_path = "/etc/network/interfaces"

        try:
            with open(config_path, 'r') as file:
                lines = file.readlines()

            ip, netmask, gateway = "", "", ""
            is_target_interface = False

            for line in lines:
                if line.startswith(f"auto {interface}"):
                    is_target_interface = True
                elif is_target_interface:
                    if line.startswith("auto") or line.strip() == "":
                        break
                    elif "address" in line:
                        ip = line.split()[-1]
                    elif "netmask" in line:
                        netmask = line.split()[-1]
                    elif "gateway" in line:
                        gateway = line.split()[-1]

            # Обновление полей ввода
            self.ip_entry.delete(0, END)
            self.ip_entry.insert(0, ip)

            self.netmask_entry.delete(0, END)
            self.netmask_entry.insert(0, netmask)

            self.gateway_entry.delete(0, END)
            self.gateway_entry.insert(0, gateway)

        except FileNotFoundError:
            messagebox.showwarning("Warning", f"Configuration file {config_path} not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")


    def apply_static_config(self):
        interface = self.interface_combobox.get()
        ip_address = self.ip_entry.get()
        netmask = self.netmask_entry.get()
        gateway = self.gateway_entry.get()

        if not (interface and ip_address and netmask):
            messagebox.showerror("Input Error", "Please fill all fields")
            return

        try:
            config = f"""auto {interface}
iface {interface} inet static
    address {ip_address}
    netmask {netmask}
"""
            # Если указан шлюз, добавляем его в конфигурацию
            if gateway:
                config += f"    gateway {gateway}\n"

            self.update_network_config(interface, config)
            messagebox.showinfo("Success", f"Static configuration applied to {interface}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply static configuration: {e}")

    def apply_dhcp_config(self):
        interface = self.interface_combobox.get()

        if not interface:
            messagebox.showerror("Input Error", "Please select an interface")
            return

        try:
            config = f"""auto {interface}
iface {interface} inet dhcp
"""
            self.update_network_config(interface, config)
            messagebox.showinfo("Success", f"DHCP configuration applied to {interface}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply DHCP configuration: {e}")

    def update_network_config(self, interface, config):
        config_path = "/etc/network/interfaces"
        try:
            # Чтение текущего конфига
            with open(config_path, 'r') as file:
                lines = file.readlines()

            # Удаление старой конфигурации интерфейса
            with open(config_path, 'w') as file:
                skip = False
                for line in lines:
                    if line.startswith(f"auto {interface}"):
                        skip = True
                    elif skip and line.startswith("auto"):
                        skip = False
                    if not skip:
                        file.write(line)

                # Добавление новой конфигурации
                file.write(config)

            # Перезапуск сети
            subprocess.run(["sudo", "service", "networking", "restart"], check=True)
        except Exception as e:
            raise Exception(f"Failed to update network configuration: {e}")

if __name__ == "__main__":
    NetworkConfigurator()