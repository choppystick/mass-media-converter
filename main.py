import tkinter as tk
from tkinter import filedialog, messagebox
from compressor.text_compressor import TextCompressor
from compressor.image_compressor import ImageCompressor
from compressor.audio_compressor import AudioCompressor
from compressor.huffman import huffman_decode
import os


class CombinedApp:
    def __init__(self, master):
        self.master = master
        master.title("Compression and Decompression Tool")
        self.create_main_menu()

    def create_main_menu(self):
        self.clear_window()
        tk.Label(self.master, text="Choose an operation:").pack(pady=10)
        tk.Button(self.master, text="Compress", command=self.show_compression_gui).pack(pady=5)
        tk.Button(self.master, text="Decompress", command=self.show_decompression_gui).pack(pady=5)

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def show_compression_gui(self):
        self.clear_window()
        tk.Button(self.master, text="Back to Main Menu", command=self.create_main_menu).pack(pady=5)

        tk.Label(self.master, text="Input File:").pack()
        self.input_entry = tk.Entry(self.master, width=50)
        self.input_entry.pack()
        tk.Button(self.master, text="Browse", command=self.select_file).pack()

        self.file_type_var = tk.StringVar(value="image")
        tk.Label(self.master, text="File Type:").pack()
        tk.Radiobutton(self.master, text="Text", variable=self.file_type_var, value="text").pack()
        tk.Radiobutton(self.master, text="Image", variable=self.file_type_var, value="image").pack()
        tk.Radiobutton(self.master, text="Audio", variable=self.file_type_var, value="audio").pack()

        self.compression_method = tk.StringVar(value="lossless")
        tk.Label(self.master, text="Compression Method:").pack()
        tk.Radiobutton(self.master, text="Lossless", variable=self.compression_method, value="lossless").pack()
        tk.Radiobutton(self.master, text="Quality Lossy", variable=self.compression_method, value="quality").pack()
        tk.Radiobutton(self.master, text="Performance Lossy", variable=self.compression_method,
                       value="performance").pack()

        tk.Button(self.master, text="Compress", command=self.compress).pack()

    def show_decompression_gui(self):
        self.clear_window()
        tk.Button(self.master, text="Back to Main Menu", command=self.create_main_menu).pack(pady=5)

        tk.Label(self.master, text="Compressed File:").pack()
        self.input_entry = tk.Entry(self.master, width=50)
        self.input_entry.pack()
        tk.Button(self.master, text="Browse", command=self.select_file).pack()

        tk.Button(self.master, text="Decompress", command=self.decompress).pack()

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("All files", "*.*"), ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                       ("Text files", "*.txt"), ("WAV files", "*.wav"), ("Binary files", "*.bin")])
        if file_path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, file_path)

    def compress(self):
        input_path = self.input_entry.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an input file.")
            return

        file_type = self.file_type_var.get()
        method = self.compression_method.get()

        if file_type == "text":
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            compressed_data = TextCompressor.compress(text, method)
            output_path = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=[("Binary files", "*.bin")])
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(compressed_data)
        elif file_type == "image":
            output_path = filedialog.asksaveasfilename(
                defaultextension=".tif" if method == "lossless" else ".jpg",
                filetypes=[("TIFF files", "*.tif"), ("JPEG files", "*.jpg")]
            )
            if output_path:
                ImageCompressor.compress(input_path, output_path, method)
        elif file_type == "audio":
            output_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
            if output_path:
                AudioCompressor.compress(input_path, output_path, method)

        if 'output_path' in locals():
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            messagebox.showinfo("Success", f"File compressed and saved to {output_path}\n"
                                           f"Original size: {original_size} bytes\n"
                                           f"Compressed size: {compressed_size} bytes\n"
                                           f"Compression ratio: {compression_ratio:.2f}%")

    def decompress(self):
        input_path = self.input_entry.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an input file.")
            return

        try:
            with open(input_path, 'rb') as f:
                compressed_data = f.read()

            decompressed_text = huffman_decode(compressed_data)

            output_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(decompressed_text)
                compressed_size = os.path.getsize(input_path)
                decompressed_size = os.path.getsize(output_path)
                messagebox.showinfo("Success", f"File decompressed and saved to {output_path}\n"
                                               f"Compressed size: {compressed_size} bytes\n"
                                               f"Decompressed size: {decompressed_size} bytes")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during decompression: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CombinedApp(root)
    root.mainloop()