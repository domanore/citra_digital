import tkinter as tk    #library untuk GUI
from tkinter import filedialog, ttk, messagebox   #library untuk dialog file dan widget
import cv2 #library untuk pengolahan gambar
from PIL import Image, ImageTk  #library untuk manipulasi gambar
import numpy as np  #library untuk manipulasi array
from matplotlib import pyplot as plt    #library untuk plotting grafik

# Kompatibilitas resampling untuk versi Pillow lama dan baru
try:    
    resample_method = Image.Resampling.LANCZOS  # Pillow >= 10.0
except AttributeError:      
    resample_method = Image.ANTIALIAS  # Pillow < 10.0

class ImageEditor:  #kelas utama untuk aplikasi pengolah gambar
    def __init__(self, root):   #inisialisasi aplikasi
        self.root = root    
        self.root.title("Aplikasi Pengolah Gambar") #judul aplikasi

        # Variabel utama
        self.original_image = None  #gambar asli
        self.processed_image = None   #gambar hasil olahan
        self.zoom_level = 1.0   #level zoom
        self.zoom_center = None #titik pusat zoom
        self.drag_start = None  #titik awal drag
        self.img_tk_original = None #gambar asli dalam format Tkinter
        self.img_tk_processed = None   #gambar hasil olahan dalam format Tkinter

        # Frame utama GUI
        main_frame = tk.Frame(self.root) #frame utama
        main_frame.pack(fill=tk.BOTH, expand=True)  #mengatur frame agar mengisi seluruh jendela

        # Kiri: Gambar asli
        frame_original = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)   #frame untuk gambar asli
        frame_original.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)    

        tk.Label(frame_original, text="Gambar Asli", font=("Arial", 12, "bold")).pack(pady=5)   #label untuk gambar asli
        self.canvas_original = tk.Canvas(frame_original, bg='gray', width=400, height=400)  #canvas untuk menampilkan gambar asli
        self.canvas_original.pack(padx=10, pady=5)  #mengatur padding untuk canvas
        ttk.Button(frame_original, text="Histogram Asli", command=self.show_original_histogram).pack(pady=2) #tombol untuk menampilkan histogram gambar asli

        # Tombol Transfer >>
        tk.Button(main_frame, text="Transfer", font=("Arial", 14), command=self.transfer_image).pack(side=tk.LEFT, pady=10) #tombol untuk mentransfer gambar asli ke gambar hasil olahan

        # Kanan: Gambar manipulasi  
        frame_edit = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)   #frame untuk gambar hasil olahan
        frame_edit.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)  #mengatur frame agar mengisi seluruh jendela

        tk.Label(frame_edit, text="Gambar Manipulasi", font=("Arial", 12, "bold")).pack(pady=5)  #label untuk gambar hasil olahan
        self.canvas_processed = tk.Canvas(frame_edit, bg='gray', width=400, height=400) #canvas untuk menampilkan gambar hasil olahan
        self.canvas_processed.pack(padx=10, pady=5) #mengatur padding untuk canvas

        # Interaksi drag untuk zoom
        self.canvas_processed.bind("<Button-1>", self.start_drag)   #mengatur event untuk drag
        self.canvas_processed.bind("<B1-Motion>", self.do_drag) #mengatur event untuk drag
        self.canvas_processed.bind("<ButtonRelease-1>", self.end_drag)  #mengatur event untuk drag

        ttk.Button(frame_edit, text="Histogram Manipulasi", command=self.show_histogram).pack(pady=2) #tombol untuk menampilkan histogram gambar hasil olahan

        # Tombol kontrol atas
        control_frame = ttk.Frame(self.root)    #frame untuk kontrol
        control_frame.pack(fill=tk.X, pady=5)   #mengatur frame agar mengisi seluruh jendela

        ttk.Button(control_frame, text="Upload", command=self.open_image).pack(side=tk.LEFT, padx=5) #tombol untuk mengupload gambar
        ttk.Button(control_frame, text="Reset", command=self.reset_image).pack(side=tk.LEFT, padx=5) #tombol untuk mereset gambar
        ttk.Button(control_frame, text="Save", command=self.save_image).pack(side=tk.LEFT, padx=5)  #tombol untuk menyimpan gambar hasil olahan
        ttk.Button(control_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=5)  #tombol untuk zoom in
        ttk.Button(control_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=5) #tombol untuk zoom out

        # Slider kontrol
        slider_frame = ttk.Frame(self.root) #frame untuk slider
        slider_frame.pack(fill=tk.X, pady=5) #mengatur frame agar mengisi seluruh jendela

        ## Slider untuk brightness
        ttk.Label(slider_frame, text="Brightness").pack(side=tk.LEFT, padx=(10, 5))
        self.brightness = tk.Scale(slider_frame, from_=-100, to=100, orient=tk.HORIZONTAL, command=self.update_image) #slider untuk brightness
        self.brightness.set(0)  #nilai default brightness
        self.brightness.pack(side=tk.LEFT)#mengatur slider agar mengisi seluruh jendela

        ## Slider untuk illumination
        ttk.Label(slider_frame, text="Illumination").pack(side=tk.LEFT, padx=(20, 5)) #label untuk illumination
        self.illumination = tk.Scale(slider_frame, from_=-1.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_image) #slider untuk illumination
        self.illumination.set(0) #nilai default illumination
        self.illumination.pack(side=tk.LEFT) #mengatur slider agar mengisi seluruh jendela

        ## Slider untuk contrast
        ttk.Label(slider_frame, text="Contrast").pack(side=tk.LEFT, padx=(20, 5)) #label untuk contrast
        self.contrast = tk.Scale(slider_frame, from_=-1.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_image)#slider untuk contrast
        self.contrast.set(0)#nilai default contrast
        self.contrast.pack(side=tk.LEFT)#mengatur slider agar mengisi seluruh jendela

    # Membuka file gambar dan menampilkan ke panel kiri
    def open_image(self): #fungsi untuk membuka file gambar
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")]) #mengatur file dialog untuk membuka file gambar
        if file_path: #jika file_path tidak kosong
            image = cv2.imread(file_path) #membaca gambar menggunakan opencv
            if image is None: #jika gambar tidak dapat dibaca
                messagebox.showerror("Error", "Gagal membuka gambar.") #menampilkan pesan error
                return  #jika gambar tidak dapat dibaca
            self.original_image = image #menyimpan gambar asli
            h, w = image.shape[:2] #mengambil ukuran gambar
            self.zoom_center = (w // 2, h // 2) #mengatur titik pusat zoom
            self.reset_sliders() #mereset slider ke nilai default
            self.zoom_level = 1.0 #mengatur level zoom ke 1.0
            self.display_image(self.original_image, self.canvas_original, 'original') #menampilkan gambar asli pada canvas

    # Mentransfer gambar asli ke bagian manipulasi
    def transfer_image(self): #fungsi untuk mentransfer gambar asli ke bagian manipulasi
        if self.original_image is not None: #jika gambar asli tidak kosong
            self.processed_image = self.original_image.copy() #menyalin gambar asli ke gambar hasil olahan
            self.zoom_level = 1.0 #mengatur level zoom ke 1.0
            h, w = self.processed_image.shape[:2]  #mengambil ukuran gambar hasil olahan
            self.zoom_center = (w // 2, h // 2) #mengatur titik pusat zoom
            self.display_image(self.processed_image, self.canvas_processed, 'processed') #menampilkan gambar hasil olahan pada canvas

    # Menampilkan gambar pada canvas
    def display_image(self, image, canvas, mode='processed'):   #fungsi untuk menampilkan gambar pada canvas
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  #mengubah format gambar dari BGR ke RGB
        h, w = image.shape[:2]  #mengambil ukuran gambar

        if mode == 'processed' and self.zoom_level > 1.0 and self.zoom_center is not None:  #jika mode adalah processed dan level zoom lebih dari 1.0
            zoom_factor = self.zoom_level   #mengatur level zoom
            center_x, center_y = self.zoom_center   #mengambil titik pusat zoom

            crop_w = int(w / zoom_factor)   #mengatur ukuran crop sesuai dengan zoom level
            crop_h = int(h / zoom_factor)   #mengatur ukuran crop sesuai dengan zoom level

            x1 = max(0, center_x - crop_w // 2) #memotong gambar sesuai dengan zoom level dan titik pusat zoom
            y1 = max(0, center_y - crop_h // 2) #memotong gambar sesuai dengan zoom level dan titik pusat zoom
            x2 = min(w, center_x + crop_w // 2) #memotong gambar sesuai dengan zoom level dan titik pusat zoom
            y2 = min(h, center_y + crop_h // 2) #memotong gambar sesuai dengan zoom level dan titik pusat zoom

            image_rgb = image_rgb[y1:y2, x1:x2] #memotong gambar sesuai dengan zoom level dan titik pusat zoom

        img_pil = Image.fromarray(image_rgb)    #mengubah gambar dari format OpenCV ke format PIL
        img_pil = img_pil.resize((400, 400), resample_method)   #mengubah ukuran gambar agar sesuai dengan ukuran canvas
        img_tk = ImageTk.PhotoImage(img_pil)    #mengubah gambar ke format Tkinter

        canvas.delete("all")    #menghapus gambar sebelumnya pada canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)   #menampilkan gambar pada canvas

        if mode == 'original':  #jika mode adalah original
            self.img_tk_original = img_tk   #menyimpan gambar asli dan hasil olahan dalam format Tkinter
        else:  # processed
            self.img_tk_processed = img_tk  #menyimpan gambar asli dan hasil olahan dalam format Tkinter

    # Fungsi utama untuk mengatur brightness, contrast, illumination
    def apply_adjustments(self):
        image = self.processed_image.copy().astype(np.float32)  #menyalin gambar hasil olahan ke variabel image dan mengubah tipe data menjadi float32
        brightness_val = self.brightness.get()  #mengambil nilai dari slider brightness, illumination, contrast
        illumination_val = self.illumination.get()  #mengambil nilai dari slider brightness, illumination, contrast
        contrast_val = self.contrast.get()  #mengambil nilai dari slider brightness, illumination, contrast

        image += brightness_val + illumination_val * 100    #fungsi untuk mengatur brightness, contrast, illumination

        factor = (259 * (contrast_val * 100 + 255)) / (255 * (259 - contrast_val * 100))    #fungsi untuk mengatur brightness, contrast, illumination
        image = factor * (image - 128) + 128    #fungsi untuk mengatur brightness, contrast, illumination

        image = np.clip(image, 0, 255).astype(np.uint8) #mengatur nilai piksel agar tidak melebihi 255
        return image    #fungsi untuk mengatur brightness, contrast, illumination

    # Update tampilan setelah slider digeser
    def update_image(self, event=None): #fungsi untuk memperbarui tampilan setelah slider digeser
        if self.processed_image is not None:    #jika gambar hasil olahan tidak kosong
            adjusted = self.apply_adjustments() #mengambil gambar hasil olahan
            self.display_image(adjusted, self.canvas_processed, 'processed')    #menampilkan gambar hasil olahan pada canvas

    # Reset ke gambar asli
    def reset_image(self):  #fungsi untuk mereset gambar ke gambar asli
        if self.original_image is not None:   #jika gambar asli tidak kosong
            self.processed_image = self.original_image.copy()   #menyalin gambar asli ke gambar hasil olahan
            self.reset_sliders()    #mereset slider ke nilai default
            h, w = self.processed_image.shape[:2]   #mengambil ukuran gambar hasil olahan
            self.zoom_center = (w // 2, h // 2) # default zoom center
            self.zoom_level = 1.0   #mengatur level zoom ke 1.0
            self.display_image(self.processed_image, self.canvas_processed, 'processed')    #menampilkan gambar asli pada canvas

    # Reset slider ke nilai default
    def reset_sliders(self):    #fungsi untuk mereset slider ke nilai default
        self.brightness.set(0)   #mereset slider ke nilai default
        self.contrast.set(0)    #mereset slider ke nilai default
        self.illumination.set(0)    #mereset slider ke nilai default

    # Simpan gambar hasil manipulasi
    def save_image(self):   #fungsi untuk menyimpan gambar hasil olahan
        if self.processed_image is not None:    #jika gambar hasil olahan tidak kosong
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])   #mengatur file dialog untuk menyimpan file gambar
            if file_path:
                adjusted = self.apply_adjustments()   #mengambil gambar hasil olahan
                cv2.imwrite(file_path, adjusted)    #menyimpan gambar hasil olahan
                messagebox.showinfo("Berhasil", "Gambar berhasil disimpan.")    #menampilkan pesan berhasil

    # Tampilkan histogram hasil manipulasi
    def show_histogram(self):   #fungsi untuk menampilkan histogram hasil manipulasi
        if self.processed_image is not None:    #jika gambar hasil olahan tidak kosong
            image = self.apply_adjustments()    #fungsi untuk menampilkan histogram hasil manipulasi
            self.plot_histogram(image, "Histogram Manipulasi")  #fungsi untuk menampilkan histogram hasil manipulasi

    # Tampilkan histogram gambar asli
    def show_original_histogram(self):  #fungsi untuk menampilkan histogram gambar asli
        if self.original_image is not None:     #jika gambar asli tidak kosong
            self.plot_histogram(self.original_image, "Histogram Asli")  #fungsi untuk menampilkan histogram gambar asli

    # Plot histogram   
    def plot_histogram(self, image, title): #fungsi untuk menampilkan histogram
        color = ('b', 'g', 'r') #warna histogram
        plt.figure(title)   #membuat figure baru untuk histogram
        plt.clf()   #membersihkan figure sebelumnya
        for i, col in enumerate(color): #mengatur warna histogram
            histr = cv2.calcHist([image], [i], None, [256], [0, 256]) #menghitung histogram untuk setiap channel warna
            plt.plot(histr, color=col)  #menghitung histogram untuk setiap channel warna   
            plt.xlim([0, 256])  #mengatur batas sumbu x
        plt.title(title)    #judul histogram
        plt.xlabel("Intensitas")    #label sumbu x dan y
        plt.ylabel("Jumlah Piksel")     #label sumbu x dan y
        plt.grid(True)  #menampilkan grid pada histogram
        plt.tight_layout()  #mengatur layout agar lebih rapi
        plt.show()  #menampilkan histogram

    # Zoom
    def zoom_in(self):  #fungsi untuk zoom in
        self.zoom_level += 0.2  #menambah level zoom
        self.update_image() #fungsi untuk zoom in

    def zoom_out(self):   #fungsi untuk zoom out
        self.update_image()# fungsi untuk zoom out

    # Drag canvas untuk navigasi zoom
    def start_drag(self, event):    #fungsi untuk memulai drag
        self.drag_start = (event.x, event.y)    #menyimpan titik awal drag

    #fungsi untuk memulai drag
    def do_drag(self, event):   #fungsi untuk melakukan drag
        if self.drag_start and self.zoom_center:    #jika drag_start dan zoom_center tidak kosong
            dx = event.x - self.drag_start[0]   #pergeseran drag
            dy = event.y - self.drag_start[1] #pergeseran drag
            scale = 400 / (self.processed_image.shape[1] / self.zoom_level) # scale factor
            dx = int(dx / scale) #menghitung pergeseran drag
            dy = int(dy / scale) #menghitung pergeseran drag
            cx, cy = self.zoom_center #ambil titik pusat zoom
            self.zoom_center = (cx - dx, cy - dy) #memperbarui zoom_center
            self.drag_start = (event.x, event.y) #memperbarui drag_start
            self.update_image() #memperbarui gambar setelah drag

    def end_drag(self, event):  #fungsi untuk mengakhiri drag
        self.drag_start = None  #mengatur drag_start ke None

# Jalankan aplikasi
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditor(root)
    root.mainloop()
