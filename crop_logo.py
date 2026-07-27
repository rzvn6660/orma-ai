from PIL import Image, ImageDraw

def circular_crop_and_transparent(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    
    # Create a mask
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # We need to find the bounding box of the non-white/non-black colored pixels
    data = img.getdata()
    width, height = img.size
    
    min_x, max_x = width, 0
    min_y, max_y = height, 0
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = data[y * width + x]
            # Not white and not black -> colored pixel
            if not (r > 240 and g > 240 and b > 240) and not (r < 15 and g < 15 and b < 15):
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                
    if max_x < min_x or max_y < min_y:
        print("Could not detect colored region.")
        return
        
    # Draw a circle on the mask bounding box
    # Slightly reduce to remove edge artifacts
    padding = 2
    bbox = [min_x + padding, min_y + padding, max_x - padding, max_y - padding]
    draw.ellipse(bbox, fill=255)
    
    # Apply the mask to the image
    result = Image.new("RGBA", img.size)
    result.paste(img, (0, 0), mask=mask)
    
    # Crop the image to the bounding box
    cropped = result.crop((min_x, min_y, max_x, max_y))
    cropped.save(output_path, "PNG")
    print("Saved cropped circular logo to", output_path)

circular_crop_and_transparent("C:/Users/rizvi/orma-ai/frontend/public/logo.png", "C:/Users/rizvi/orma-ai/frontend/public/logo-transparent.png")
