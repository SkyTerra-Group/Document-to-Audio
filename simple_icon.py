"""
Simple icon creator that doesn't require PIL - creates a basic ICO file
"""
import struct

def create_simple_ico():
    """Create a very basic 32x32 icon file"""
    
    # ICO file header (6 bytes)
    ico_header = struct.pack('<HHH', 0, 1, 1)  # Reserved, Type (1=ICO), Count
    
    # Icon directory entry (16 bytes)
    width = 32
    height = 32
    colors = 0  # 0 means 256+ colors
    reserved = 0
    planes = 1
    bit_count = 32  # 32-bit RGBA
    image_size = width * height * 4 + 40  # 40 bytes for BITMAPINFOHEADER
    image_offset = 22  # 6 (header) + 16 (directory entry)
    
    ico_entry = struct.pack('<BBBBHHLL', 
                           width, height, colors, reserved,
                           planes, bit_count, image_size, image_offset)
    
    # BITMAPINFOHEADER (40 bytes)
    bitmap_header = struct.pack('<LLLHHLLLLLL',
                               40,  # header size
                               width,  # width
                               height * 2,  # height (doubled for icon)
                               1,  # planes
                               bit_count,  # bits per pixel
                               0,  # compression
                               width * height * 4,  # image size
                               0, 0, 0, 0)  # other fields
    
    # Create simple pixel data (blue document with orange sound waves)
    pixels = []
    for y in range(height):
        for x in range(width):
            # Create a simple document icon pattern
            if 8 <= x <= 20 and 4 <= y <= 28:  # Document area
                if y == 4 and x >= 18:  # Folded corner
                    pixels.extend([200, 200, 200, 255])  # Light gray
                elif 12 <= y <= 26 and x in [10, 12, 14, 16, 18]:  # Text lines
                    pixels.extend([255, 255, 255, 255])  # White text
                else:
                    pixels.extend([70, 130, 180, 255])  # Steel blue document
            elif 22 <= x <= 30 and abs(y - 16) <= (x - 22) * 0.5:  # Sound waves
                pixels.extend([255, 140, 0, 255])  # Orange sound
            else:
                pixels.extend([0, 0, 0, 0])  # Transparent background
    
    # Convert RGBA to BGRA (Windows format)
    bgra_pixels = []
    for i in range(0, len(pixels), 4):
        r, g, b, a = pixels[i:i+4]
        bgra_pixels.extend([b, g, r, a])
    
    # Write ICO file
    with open('document_to_speech.ico', 'wb') as f:
        f.write(ico_header)
        f.write(ico_entry)
        f.write(bitmap_header)
        f.write(bytes(bgra_pixels))
    
    print("Simple icon created: document_to_speech.ico")

if __name__ == "__main__":
    create_simple_ico()