# BMP Image Editor & Compressor

 A Python appicaiton built with Tkinter and Pillow (PIL) that can:
 - Open and parse '.bmp' (bitmap) images munually.
 - Adjust brightness and scale images.
- Compress and decompress images using LZW algorithm.
 - Toggle individual color channels (Red, Green, Blue).

 # What It Does

 **Manual BMP Parsing**
 - Reads raw BMP headers and pixel data (no external library used).
 - Supports 1-bit, 4-bit, 8-bit and 24-bit.

**Image Editing**
- Adjust brightness by adjusting the RGB values that was parsed.
- Slider to scale image directly from parsed pixels.
- Toggle individual RGB color channels.

**LZW Compression**
- Implemented with LZW lossless compression algorithm.

**Custom GUI**
- Built with Tkinter
- Clean and clear layout.
