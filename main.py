import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import os
import math
import struct

from compression import lzw_compression, lzw_decompression
from time import sleep, time
from threading import Thread
from tkinter import PhotoImage
from  PIL import Image, ImageTk

# helper functions to find important metadataS
def get_file_size(bmp_bytes):
    return int.from_bytes(bmp_bytes[2:6], 'little')

def get_width(bmp_bytes):
    return int.from_bytes(bmp_bytes[18:22], 'little')

def get_height(bmp_bytes):
    return int.from_bytes(bmp_bytes[22:26], 'little')

def get_bits_per_pixel(bmp_bytes):
    return int.from_bytes(bmp_bytes[28:30], 'little')

def get_offset(bmp_bytes):
    return int.from_bytes(bmp_bytes[10:14], 'little')

def get_compression(bmp_bytes):
    return int.from_bytes(bmp_bytes[30:34], 'little')

def get_color_table(bmp_bytes, bpp):
    color_table = []
    if bpp <= 8:
        num_of_color = 2 ** bpp
        info_size = int.from_bytes(bmp_bytes[14:18], 'little')
        color_table_offset = 14 + info_size     # 14 for header and 40 for infoheader size

        for i in range(num_of_color):
            offset = color_table_offset + i * 4
            blue = bmp_bytes[offset]
            green = bmp_bytes[offset + 1]
            red = bmp_bytes[offset + 2]
            color_table.append((red, green, blue))     # store rgb values

    return color_table

def parse_pixel(bmp_bytes, width, height, bpp, data_offset, color_table):
    pixel = []

    bytes_per_row = (width * bpp + 31) // 32 * 4   # include padding to make sure it is to the nearest 4 byte
    h = height

    for y in range(h):
        file_row = h - 1 - y
        start_row = data_offset + file_row * bytes_per_row
        end_row = start_row
        row_data = bmp_bytes[start_row : start_row + bytes_per_row]     # the specific position for the color value

        row_colors = []

        if bpp == 8:
            for x in range(width):
                # the index is the color value 
                value = row_data[x]
                row_colors.append(color_table[value])
        
        elif bpp == 4:
            for x in range(width):
                byte = x // 2         # for 4bpp each pixel holds half a byte => 2 pixels per byte
                value = row_data[byte]

                if x % 2 == 0:
                    index = value // 16     # first 4 bytes
                else:
                    index = value % 16      # second 4 bytes
                row_colors.append(color_table[index])

        elif bpp == 1:
            for x in range(width):
                byte = x // 8        
                value = row_data[byte]
                position = 7 - (x % 8)
                index = (value >> position) & 1     # keep the lowest bit to get 1 or 0
                row_colors.append(color_table[index])
        
        pixel.append(row_colors)

    return pixel

# function to change brightness of image by directly changeing the rgb values directly (for 24bpp)
def brightness_changer(value):
    if not hasattr(image_label, "original_image"):
        return
    
    brightness = int(value) / 100

    img = image_label.original_image.copy()
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            red, green, blue = pixels[x, y]
            red = int(red * brightness)
            green = int(green * brightness)
            blue = int(blue * brightness)
            pixels[x, y] = (min(255, red), min(255, green), min(255, blue))
    
    tk_img = ImageTk.PhotoImage(img)
    image_label.config(image=tk_img)
    image_label.image = tk_img

    return

def scale_changer(value):
    if not hasattr(image_label, "original_image"):
        return
    
    img = image_label.original_image
    original_w = image_label.original_width
    original_h = image_label.original_height

    scale = int(value) / 100
    if scale <= 0:
        return 

    new_w = int(original_w * scale)
    new_h = int(original_h * scale) 
    
    new_img = Image.new("RGB", (new_w, new_h))
    original_pixel = img.load()
    new_pixel = new_img.load()

    for y in range(new_h):
        for x in range(new_w):
            w = int(x / scale)
            h = int(y / scale)
            new_pixel[x, y] = original_pixel[w, h]
        
    tk_img = ImageTk.PhotoImage(new_img)
    image_label.config(image=tk_img)
    image_label.image = tk_img

    return

def rgb_changer():
    if not hasattr(image_label, "original_image"):
        return
    
    img = image_label.original_image.copy()
    pixels = img.load()

    red = bool(red_val.get())
    green = bool(green_val.get())
    blue = bool(blue_val.get())

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            if not red:
                r = 0
            if not green:
                g = 0
            if not blue:
                b = 0
            pixels[x, y] = (r, g, b)
    
    tk_img = ImageTk.PhotoImage(img)
    image_label.config(image=tk_img)
    image_label.image = tk_img

    return

def display_bmp_image(bmp_bytes, filepath):
    file_size = get_file_size(bmp_bytes)
    width = get_width(bmp_bytes)
    height = get_height(bmp_bytes)
    bits_per_pixel = get_bits_per_pixel(bmp_bytes)
    offset = get_offset(bmp_bytes)
    compression = get_compression(bmp_bytes)

    show_metadata(
        metadata,
        file_size=file_size,
        width=width,
        height=height,
        bpp=bits_per_pixel,
    )

    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, filepath)

    # load the image using the parser depending on the bpp
    if bits_per_pixel in (1, 4, 8):
        if compression != 0:
            return 
        
        color_table = get_color_table(bmp_bytes, bits_per_pixel)
        pixels = parse_pixel(
            bmp_bytes=bmp_bytes,
            width=width,
            height=height,
            bpp=bits_per_pixel,
            data_offset=offset,
            color_table=color_table
        )

        # load the image using the color parsed from each image
        image = Image.new("RGB", (width, height))
        for y in range(height):
            for x in range(width):
                image.putpixel((x, y), pixels[y][x])
        original_image = image

    elif bits_per_pixel == 24:
        # original_image = Image.open(filepath).convert("RGB")
        # -> could use this but in PA we need to open .cmpt365 file and Image doesnt support it so we have to do it manually

        bytes_per_pixel = 3
        bytes_per_row = (width * bytes_per_pixel + 3) // 4 * 4

        image = Image.new("RGB", (width, height))

        # parse pixel manually
        for y in range(height):
            row_y = height - 1 - y
            row_start = offset + row_y * bytes_per_row

            for x in range(width):
                pixel_start = row_start + x * bytes_per_pixel
                blue_val = bmp_bytes[pixel_start]
                green_val = bmp_bytes[pixel_start + 1]
                red_val = bmp_bytes[pixel_start + 2]
                image.putpixel((x, y), (red_val, green_val, blue_val))
        
        original_image = image

    # save original height, width and image to use later
    image_label.original_image = original_image
    image_label.original_width = width 
    image_label.original_height = height

    tk_image = ImageTk.PhotoImage(original_image)   
    image_label.config(image=tk_image)
    image_label.image = tk_image

    # show the feature after the image is loaded   
    brightness_bar.config(state="normal") 
    scaler_bar.config(state="normal")
    red.config(state="normal")
    green.config(state="normal")
    blue.config(state="normal")

    brightness_bar.set(100)
    scaler_bar.set(100)

def browse_file():
    filepath = tk.filedialog.askopenfilename()

    # check file type 
    _, file_extension = os.path.splitext(filepath)

    if file_extension.lower() != ".bmp":
        tk.messagebox.showerror("Invalid File Type", "Please select a BMP file.")
        return

    # parse bpm file
    with open(filepath, "rb") as f:
        bmp_bytes = f.read()

    display_bmp_image(bmp_bytes, filepath)

# -----------------------------------------PA2-----------------------------------------
def display_decompressed_image(bmp, filepath):
    display_bmp_image(bmp, filepath)

def start_compression():
    Thread(target=compress_file).start()

def start_decompression():
    Thread(target=decompress_file).start()

def compress_file():
    print("compress button is clicked!")
    if not hasattr(image_label, "original_image"):
        tk.messagebox.showerror("Error", "Please choose an image to compress!")
        return
    
    filepath = file_path_entry.get()
    if not filepath:
        tk.messagebox.showerror("Error", "No file selected")
        return

    with open(filepath, "rb") as f:
        bmp = f.read()
    
    original_size = len(bmp)

    # start timer
    timer = time()

    bpp = get_bits_per_pixel(bmp)
    offset = get_offset(bmp)

    if bpp == 24:
        # get the raw data straight
        pixel = bmp[offset:]
        print(f"pixel data size: {len(pixel)}")
        compressed = lzw_compression(pixel)
        print(f"after compression: {len(compressed)}")
    else:
        pass

    compression_time = (time() - timer) * 1000
    print(f"compression time: {compression_time:.2f} ms")

    output = create_file(bmp, compressed)

    output_path = filepath.replace(".bmp", ".cmpt365")
    with open(output_path, "wb") as f:
        f.write(output)

    compressed_size = len(output)
    ratio = compressed_size / original_size

def decompress_file():
    # open .cmpt365 file
    print("open .cmpt365 button is clicked!")

    filepath = tk.filedialog.askopenfilename()

    #check fle type
    _, file_extension = os.path.splitext(filepath)

    if file_extension.lower() != ".cmpt365":
        tk.messagebox.showerror("Invalid File Type", "Please select .cmpt365 file.")
        return
    
    with open(filepath, "rb") as f:
        metadata = f.read()

    """
    [0-7]   [for ISCMP365]
    [8-11]  [algorithm code]
    [12-15] [width]
    [16-19] [height]
    [20-23] [bpp]
    [24-27] [num of compressed codes]
    """

    # check if valid header 
    algo_id = struct.unpack_from("<I", metadata, 8)[0]
    width = struct.unpack_from("<I", metadata, 12)[0]
    height = struct.unpack_from("<I", metadata, 16)[0]
    bpp = struct.unpack_from("<I", metadata, 20)[0]
    num_of_codes = struct.unpack_from("<I", metadata, 24)[0]

    header_size = 14 + 40
    bmp_header = metadata[28: 28 + header_size]

    compressed_codes = []
    offset = 28 + header_size
    
    for i in range(num_of_codes):
        if offset + 4 > len(metadata):
            break 
        
        code = struct.unpack_from("<I", metadata, offset)[0]
        compressed_codes.append(code)
        offset += 4

    print(f"Algorithm: {algo_id}, {width}x{height}, {bpp}bpp, {num_of_codes} codes")

    decompressed = lzw_decompression(compressed_codes)

    full_bmp = bmp_header + decompressed

    print(f"Decompression: {len(compressed_codes)} codes -> {len(decompressed)} bytes")

    display_decompressed_image(full_bmp, filepath)

def create_file(bmp, compressed):
    width = get_width(bmp)
    height = get_height(bmp)
    bpp = get_bits_per_pixel(bmp)
    offset = get_offset(bmp)

    header = bytearray()
    header.extend(b"ISCMP365")
    header.extend(struct.pack("<I", 1))                     # code for algoritm used (1 = lzw)
    header.extend(struct.pack("<I", width))
    header.extend(struct.pack("<I", height))
    header.extend(struct.pack("<I", bpp))
    header.extend(struct.pack("<I", len(compressed)))

    bmp_header = bmp[:offset]
    
    # convert compressed pixels to bytes and store them
    compressed_bytes = bytearray()
    for c in compressed:
        compressed_bytes.extend(struct.pack("<I", c))
    
    return header + bmp_header + compressed_bytes

def show_compressed_data(original_file, compressed, ratio, time):
    pass
# --------------------------------------END OF PA2--------------------------------------

# create ui for 4 metadatas and the space will be empty before inserting the file
def create_metadata(data):
    box = tk.Frame(data)
    box.grid(row=3, column=1)

    size_label = tk.Label(box, text="File Size: ")
    size_label.grid(row=0, column=0)

    width_label = tk.Label(box, text=" Width: ")
    width_label.grid(row=1, column=0)

    height_label = tk.Label(box, text="Height: ")
    height_label.grid(row=2, column=0)

    bpp_label = tk.Label(box, text="Bits Per Pixel: ")
    bpp_label.grid(row=3, column=0)

    return {
        "size": size_label,
        "width": width_label,
        "height": height_label,
        "bpp": bpp_label,
    }

# after getting the data, display it on the window
def show_metadata(labels, file_size, width, height, bpp):
    labels["size"].config(text=f"File Size: {file_size}")
    labels["width"].config(text=f"Width: {width}")
    labels["height"].config(text=f"Height: {height}")
    labels["bpp"].config(text=f"Bits Per Pixel: {bpp}")

root = tk.Tk()
root.geometry("900x700")

# ----------------------------------------GUI----------------------------------------
# code section for better GUI
# top
top = tk.Frame(root, padx=10, pady=8)
top.grid(row=0, column=0, sticky="ew")

# the centre is divided to left part and right part
center = tk.Frame(root, padx=10, pady=8)
center.grid(row=1, column=0, sticky="nsew")

left = tk.Frame(center)   # image area
left.grid(row=0, column=0, sticky="nsew", padx=(0,10))

right = tk.LabelFrame(center, padx=5, pady=5)  # brightness and scale area
right.grid(row=0, column=1, sticky="ns")

# bottom
bottom = tk.LabelFrame(root, text="Metadata", padx=10, pady=15)
bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,10))

# blank area to show image
root.grid_rowconfigure(1, weight=1)  
root.grid_columnconfigure(0, weight=1) 

center.grid_rowconfigure(0, weight=1)  
center.grid_columnconfigure(0, weight=1) 

image_label = tk.Label(left)
image_label.grid(row=0, column=1)

tk.Label(top, text="File Path").grid(row=0, column=0)
file_path_entry = tk.Entry(top, width=80)
file_path_entry.grid(row=0, column=1, sticky="ew", padx=8)
tk.Button(top, text="Browse", command=browse_file).grid(row=0, column=2)

# brightness section
brightness = tk.Label(right, text="Brightness (%)")
brightness.grid(row=1, column=1)
brightness_bar = tk.Scale(right, from_=100, to = 0, orient= "vertical", 
                          command=brightness_changer, state="disabled", length=150)
brightness_bar.set(100)
brightness_bar.grid(row=2, column=1)

# scaling section
scaler = tk.Label(right, text="Scale (%)")
scaler.grid(row=1, column=0)
scaler_bar = tk.Scale(right, from_=100, to = 0, orient= "vertical", 
                      command=scale_changer, state="disabled", length=150)
scaler_bar.set(100)
scaler_bar.grid(row=2, column=0)

# rgb toggle section 
# enable the values of red, green and blue first
rgb_box = tk.Label(right, pady=5)
rgb_box.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0))

red_val = tk.IntVar(value=1)
green_val = tk.IntVar(value=1)
blue_val = tk.IntVar(value=1)

red = tk.Checkbutton(rgb_box, text="Red", fg="red", variable=red_val, onvalue=1, offvalue=0, command=rgb_changer, state="disabled")
green = tk.Checkbutton(rgb_box, text="Green", fg="green", variable=green_val, onvalue=1, offvalue=0, command=rgb_changer, state="disabled")
blue = tk.Checkbutton(rgb_box, text="Blue", fg="blue", variable=blue_val, onvalue=1, offvalue=0, command=rgb_changer, state="disabled")

red.grid(row=0, column=0, padx=8, pady=2, sticky="w")
green.grid(row=0, column=1, padx=8, pady=2, sticky="w")
blue.grid(row=0, column=2, padx=8, pady=2, sticky="w")

# compression gui
tk.Button(right, text="Compress", command=start_compression).grid(row=5, column=0, padx="10", pady="220", sticky="s")
tk.Button(right, text="Open .cmpt365", command=start_decompression).grid(row=5, column=1, padx="10", pady="220", sticky="s")

# decompressed info
decompressed_info = tk.Label(center, text="Decompressed Info").grid(sticky="sw")

metadata = create_metadata(bottom)

root.mainloop()



