from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    document_color = (70, 130, 180)  # Steel blue
    sound_color = (255, 140, 0)     # Dark orange
    text_color = (255, 255, 255)    # White
    
    # Draw document shape (rectangle with folded corner)
    doc_left = 40
    doc_top = 30
    doc_right = 140
    doc_bottom = 200
    fold_size = 20
    
    # Main document rectangle
    draw.rectangle([doc_left, doc_top + fold_size, doc_right, doc_bottom], 
                   fill=document_color, outline=(50, 100, 150), width=3)
    
    # Folded corner
    draw.polygon([
        (doc_right - fold_size, doc_top),
        (doc_right, doc_top + fold_size),
        (doc_right - fold_size, doc_top + fold_size)
    ], fill=(50, 100, 150))
    
    # Document lines (text representation)
    line_color = (200, 220, 240)
    for i in range(4):
        y = doc_top + 50 + i * 20
        draw.rectangle([doc_left + 15, y, doc_right - 15, y + 3], fill=line_color)
    
    # Sound waves
    center_x = 180
    center_y = 120
    
    # Draw concentric arcs representing sound waves
    for i, radius in enumerate([30, 45, 60]):
        thickness = 8 - i * 2
        draw.arc([center_x - radius, center_y - radius, 
                 center_x + radius, center_y + radius], 
                start=-45, end=45, fill=sound_color, width=thickness)
    
    # Speaker cone
    speaker_points = [
        (center_x - 25, center_y - 15),
        (center_x - 25, center_y + 15),
        (center_x - 10, center_y + 8),
        (center_x - 10, center_y - 8)
    ]
    draw.polygon(speaker_points, fill=sound_color, outline=(200, 100, 0), width=2)
    
    # Arrow from document to speaker (indicating conversion)
    arrow_start_x = doc_right + 5
    arrow_end_x = center_x - 35
    arrow_y = center_y
    
    # Arrow line
    draw.line([arrow_start_x, arrow_y, arrow_end_x, arrow_y], 
              fill=(100, 100, 100), width=4)
    
    # Arrow head
    draw.polygon([
        (arrow_end_x, arrow_y - 8),
        (arrow_end_x, arrow_y + 8),
        (arrow_end_x + 12, arrow_y)
    ], fill=(100, 100, 100))
    
    # Save as ICO file with multiple sizes
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []
    
    for icon_size in icon_sizes:
        resized = img.resize(icon_size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Save as .ico file
    ico_path = 'document_to_speech.ico'
    images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
    
    # Also save as PNG for preview
    img.save('document_to_speech_icon.png', format='PNG')
    
    print(f"Icon created successfully!")
    print(f"ICO file: {ico_path}")
    print(f"PNG preview: document_to_speech_icon.png")

if __name__ == "__main__":
    try:
        create_icon()
    except ImportError:
        print("PIL (Pillow) is required to create the icon.")
        print("Install it with: pip install Pillow")
        print("\nAlternatively, you can use any image editor to create a 256x256 pixel icon")
        print("and save it as 'document_to_speech.ico' in this directory.")