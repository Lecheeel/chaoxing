from PIL import Image, ImageDraw, ImageFont
import emoji
img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("seguiemj.ttf", 24)
draw.text((4, 4), "📚", font=font, embedded_color=True)
img.save('favicon.ico', format='ICO', sizes=[(32, 32)]) 