import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import queue
import time
class ExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Explorer")
        self.current_directory = "C:/"
        self.listbox = tk.Listbox(root, bg="black", fg="white", selectbackground=None, font=("Courier", 14))
        self.listbox.pack(expand=tk.YES, fill=tk.BOTH)
        self.populate_listbox()

        self.listbox.bind("<Up>", self.move_up)
        self.listbox.bind("<Down>", self.move_down)
        self.listbox.bind("<Return>", self.open_selected)

        # Přidává inicializaci klávesnice
        self.root.bind("<Up>", self.move_up)
        self.root.bind("<Down>", self.move_down)
        self.root.bind("<Return>", self.open_selected)
        self.root.bind("<Control-c>", self.handle_ctrl_c)

        self.output_text = tk.Text(root, bg="black", fg="white", font=("Courier", 14))
        self.output_text.pack(expand=tk.YES, fill=tk.BOTH)
        self.output_queue = queue.Queue()

        # Vytvoří vlákno pro zpracování výstupu Python skriptu
        self.output_thread = Thread(target=self.process_output)
        self.output_thread.daemon = True
        self.output_thread.start()

        self.root.mainloop()

    def populate_listbox(self):
        self.listbox.delete(0, tk.END)
        items = ["back"] + sorted(os.listdir(self.current_directory))
        for item in items:
            self.listbox.insert(tk.END, item)

        # Nastavuje výchozí výběr na "back"
        self.listbox.selection_set(0)
        self.listbox.see(0)

    def move_up(self, event):
        selected_index = self.listbox.curselection()
        if selected_index and selected_index[0] > 0:
            self.listbox.selection_clear(selected_index[0])
            self.listbox.selection_set(selected_index[0] - 1)
            self.listbox.see(selected_index[0] - 1)

    def move_down(self, event):
        selected_index = self.listbox.curselection()
        if selected_index and selected_index[0] < self.listbox.size() - 1:
            self.listbox.selection_clear(selected_index[0])
            self.listbox.selection_set(selected_index[0] + 1)
            self.listbox.see(selected_index[0] + 1)

    def open_selected(self, event):
        selected_index = self.listbox.curselection()
        if not selected_index:
            return

        selected_item = self.listbox.get(selected_index)
        if selected_item == "back":
            self.go_back()
        elif os.path.isdir(os.path.join(self.current_directory, selected_item)):
            self.enter_directory(selected_item)
        elif selected_item.endswith(".py"):
            self.run_python_script(selected_item)
        else:
            messagebox.showinfo("Explorer", "Cannot open non-directory/non-Python file.")

    def go_back(self):
        self.current_directory = os.path.dirname(self.current_directory)
        self.populate_listbox()

    def enter_directory(self, directory):
        self.current_directory = os.path.join(self.current_directory, directory)
        self.populate_listbox()

    def run_python_script(self, script_name):
        script_path = os.path.join(self.current_directory, script_name)
        # Přidává do fronty informace o spuštěném skriptu
        self.output_queue.put(f"Running script: {script_path}\n")
        process = subprocess.Popen(['python', f'{script_path}'], stdout=subprocess.PIPE, text=True)
        try:
            while True:
                output = process.stdout.readline()
                if not output:
                    break
                self.output_queue.put(output.strip())
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            process.terminate()

    def process_output(self):
        while True:
            try:
                # Získává výstup ze fronty
                output = self.output_queue.get(block=True, timeout=0.1)
                # Zobrazuje výstup v textovém poli
                self.output_text.insert(tk.END, output)
                self.output_text.yview(tk.END)
            except queue.Empty:
                pass

    def handle_ctrl_c(self, event):
        # Zpracovává stisknutí Ctrl+C
        self.output_queue.put("Ctrl+C pressed\n")

if __name__ == "__main__":
    root = tk.Tk()
    explorer_app = ExplorerApp(root)
