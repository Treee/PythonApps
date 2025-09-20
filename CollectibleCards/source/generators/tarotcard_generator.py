import os
from PIL import Image

def extract_tarot_cards_grid(input_png, output_dir, cols=14, rows=6, border=2):
    # Clear the output directory
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            file_path = os.path.join(output_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    else:
        os.makedirs(output_dir, exist_ok=True)
    img = Image.open(input_png).convert('RGBA')
    width, height = img.size
    card_w = (width - (cols + 1) * border) // cols
    card_h = (height - (rows + 1) * border) // rows
    card_count = 0
    row_types = ['w', 'c', 's', 'p', 'ma', 'ma']
    for row in range(rows):
        for col in range(cols):
            if card_count >= 80:
                return
            left = border + col * (card_w + border)
            upper = border + row * (card_h + border)
            right = left + card_w
            lower = upper + card_h
            card = img.crop((left, upper, right, lower))
            # Scale card so height is 256, keep aspect ratio
            scale_factor = 256 / card.height
            new_w = int(card.width * scale_factor)
            card = card.resize((new_w, 256), Image.LANCZOS)
            out_img = Image.new('RGBA', (256, 256), (0,0,0,0))
            paste_x = 0
            paste_y = 0
            out_img.paste(card, (paste_x, paste_y))
            if card_count == 78:
                out_name = "card_back_1_co.png"
            elif card_count == 79:
                out_name = "card_back_2_co.png"
            else:
                card_type = row_types[row] if row < len(row_types) else 'x'
                out_name = f"iat_tarotcard_{card_type}_{col+1:02d}_co.png"
            out_img.save(os.path.join(output_dir, out_name))
            print(f"Saved {out_name} ({card.width}x{card.height})")
            card_count += 1

if __name__ == "__main__":
    INPUT_PNG = "source/art/tarotcards/iat_tarotcards_co.png"
    OUTPUT_DIR = "release/tarot_cards"
    extract_tarot_cards_grid(INPUT_PNG, OUTPUT_DIR, cols=14, rows=6, border=2)
