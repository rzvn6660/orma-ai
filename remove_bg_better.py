from PIL import Image

def remove_bg_better(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for item in data:
        r, g, b, a = item
        # If very close to white, make transparent
        if r > 240 and g > 240 and b > 240:
            new_data.append((255, 255, 255, 0))
        # If very close to black, make transparent
        elif r < 15 and g < 15 and b < 15:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(output_path, "PNG")

remove_bg_better("C:/Users/rizvi/orma-ai/frontend/public/logo.png", "C:/Users/rizvi/orma-ai/frontend/public/logo-transparent.png")
