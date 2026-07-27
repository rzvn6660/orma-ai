from PIL import Image

def remove_white_bg(input_path, output_path, threshold=240):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for item in data:
        # Check if the pixel is white-ish
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            # Replace with transparent
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    # Optionally crop to bounding box to remove extra padding
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        
    img.save(output_path, "PNG")

remove_white_bg("C:/Users/rizvi/orma-ai/frontend/public/logo.png", "C:/Users/rizvi/orma-ai/frontend/public/logo-transparent.png")
