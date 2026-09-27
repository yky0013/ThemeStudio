"""Real isolated shortcut files for screenshots; never changes the user's desktop."""
from pathlib import Path
from PIL import Image, ImageDraw

project = Path(__file__).resolve().parents[1]
folder = project / 'qa/runtime/tutorial-app/demo'
desktop = folder / 'desktop'
desktop.mkdir(parents=True, exist_ok=True)
for name in ['示例浏览器', '示例文档', '示例工具']:
    file = desktop / (name + '.url')
    if not file.exists():
        file.write_text('[InternetShortcut]\nURL=https://example.org/\n', encoding='utf-8')
artwork = folder / '我的图片.png'
if not artwork.exists():
    picture = Image.new('RGBA', (320, 320), (0, 0, 0, 0))
    draw = ImageDraw.Draw(picture)
    draw.rounded_rectangle((24, 24, 296, 296), radius=68, fill='#7964c3')
    draw.ellipse((110, 70, 210, 170), fill='#ffd688')
    draw.rounded_rectangle((82, 218, 238, 242), radius=12, fill='#ddd2ff')
    picture.save(artwork)
print(folder)
