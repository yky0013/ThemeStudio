"""Compile imagegen character atlases into native ICO/CUR assets and previews.

The art comes from imagegen; this compiler slices the atlas, lays out the
existing code-drawn functional glyphs, and encodes sizes and click hotspots.
"""
from pathlib import Path
import importlib.util
import io
import json
import math
import struct
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('base_assets', ROOT / 'tools/build-template-assets.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
ROLE_LABELS = ['普通选择','帮助选择','后台运行','忙碌','精确选择','文本选择','手写','不可用',
               '垂直调整','水平调整','对角调整 1','对角调整 2','移动','备用选择','链接选择','人员选择','位置选择']
ICON_LABELS = ['文件管理','浏览器','聊天','笔记','编程','科研','文献','音乐','网盘','游戏','办公','工具']
POSE_FOR_ROLE = [0,1,2,3,1,4,5,6,8,9,9,8,7,8,11,0,10]
POSE_FOR_ICON = [0,8,3,5,1,7,4,10,2,11,6,9]
SIZES = (32, 48, 64, 96)


def clean_cell(cell):
    """Discard tiny detached pieces from adjacent atlas cells; keep original RGBA."""
    width,height=cell.size
    mask=cell.getchannel('A').point(lambda a: 255 if a >= 24 else 0).tobytes()
    visited=bytearray(len(mask));components=[]
    for start in range(len(mask)):
        if not mask[start] or visited[start]:continue
        visited[start]=1;stack=[start];component=[]
        while stack:
            index=stack.pop();component.append(index)
            x=index%width;y=index//width
            for other in ((index-1 if x else -1),(index+1 if x+1<width else -1),
                          (index-width if y else -1),(index+width if y+1<height else -1)):
                if other>=0 and mask[other] and not visited[other]:
                    visited[other]=1;stack.append(other)
        components.append(component)
    largest=max((len(c) for c in components),default=0)
    if not largest:return cell
    remove=bytearray(len(mask))
    for component in components:
        touches=any(i%width in (0,width-1) or i//width in (0,height-1) for i in component)
        if len(component)<max(64,largest*.012) or (touches and len(component)<largest*.15):
            for index in component:remove[index]=255
    from PIL import ImageChops
    alpha=ImageChops.subtract(cell.getchannel('A'),Image.frombytes('L',cell.size,bytes(remove)))
    cell.putalpha(alpha)
    return cell


def sprites(atlas_path):
    with Image.open(atlas_path) as source:
        source = source.convert('RGBA')
    alpha = source.getchannel('A')
    if alpha.getextrema()[0] != 0:
        raise ValueError(f'Atlas lacks transparent pixels: {atlas_path}')
    if alpha.histogram()[0] / (source.width * source.height) < .08:
        raise ValueError(f'Atlas has insufficient transparent gutters: {atlas_path}')
    result = []
    for row in range(3):
        for col in range(4):
            cell = source.crop((round(col * source.width / 4), round(row * source.height / 3),
                                round((col + 1) * source.width / 4), round((row + 1) * source.height / 3)))
            cell = clean_cell(cell)
            bounds = cell.getchannel('A').point(lambda a: 255 if a >= 24 else 0).getbbox()
            if bounds is None:
                raise ValueError(f'Empty atlas cell {row},{col}: {atlas_path}')
            result.append(cell.crop(bounds))
    return result


def fit_character(image, size):
    image = image.copy()
    image.thumbnail(size, Image.Resampling.LANCZOS)
    return image


def functional_cursor(role, accent, pale):
    scale=4
    image = Image.new('RGBA', (128*scale, 128*scale))
    class ScaledDraw:
        def __getattr__(self,name):
            method=getattr(ImageDraw.Draw(image),name)
            def draw(points,*args,**kwargs):
                def scaled(value):
                    return [scaled(v) for v in value] if isinstance(value,(list,tuple)) else value*scale
                for key in ('width','radius'):
                    if key in kwargs:kwargs[key]=kwargs[key]*scale
                return method(scaled(points),*args,**kwargs)
            return draw
    d = ScaledDraw()
    ink = '#203038'
    def polygon(points, fill=accent):
        d.polygon(points, fill=fill, outline=ink, width=2)
    hot = (32, 32)
    if role in ('Arrow', 'AppStarting'):
        polygon([(4,4),(4,64),(20,49),(33,71),(44,64),(30,43),(57,41)])
        hot = (5,5)
        if role == 'AppStarting':
            d.ellipse((47,4,70,27),fill=pale,outline=ink,width=2)
            d.arc((51,8,66,23),-90,185,fill=accent,width=4)
    elif role == 'Help':
        d.line([(12,19),(13,12),(20,6),(35,5),(47,12),(47,23),(32,35),(30,45)],fill=ink,width=11,joint='curve')
        d.line([(12,19),(13,12),(20,6),(35,5),(47,12),(47,23),(32,35),(30,45)],fill=accent,width=7,joint='curve')
        d.ellipse((24,55,36,67),fill=accent,outline=ink,width=2)
        hot=(23,6)
    elif role == 'Wait':
        for i in range(8):
            angle=2*math.pi*i/8
            x=32+24*math.cos(angle);y=32+24*math.sin(angle)
            radius=4+i*.25
            d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=accent if i<6 else pale,outline=ink,width=1)
    elif role == 'IBeam':
        polygon([(15,5),(47,5),(47,12),(35,12),(35,59),(47,59),(47,67),(15,67),(15,59),(27,59),(27,12),(15,12)])
        hot=(31,35)
    elif role == 'Crosshair':
        d.line((32,5,32,63),fill=ink,width=8);d.line((5,32,63,32),fill=ink,width=8)
        d.line((32,5,32,63),fill=accent,width=4);d.line((5,32,63,32),fill=accent,width=4)
        d.ellipse((25,25,39,39),outline=pale,width=2)
    elif role == 'NWPen':
        polygon([(43,4),(58,18),(19,58),(5,63),(10,48)])
        d.line((16,49,48,16),fill=pale,width=3)
        hot=(7,60)
    elif role == 'No':
        d.ellipse((5,5,61,61),fill=accent,outline=ink,width=2)
        d.ellipse((14,14,52,52),fill=pale,outline=ink,width=2)
        d.line((14,52,52,14),fill=ink,width=11);d.line((14,52,52,14),fill=accent,width=7)
    elif role in ('SizeNS','SizeWE','SizeNWSE','SizeNESW','UpArrow'):
        if role == 'UpArrow':
            polygon([(32,4),(12,26),(24,26),(24,62),(40,62),(40,26),(52,26)])
            hot=(32,6)
        else:
            polygon([(32,4),(12,24),(24,24),(24,44),(12,44),(32,64),(52,44),(40,44),(40,24),(52,24)])
            small=image.crop((0,0,68*scale,68*scale))
            angle={'SizeNS':0,'SizeWE':90,'SizeNWSE':45,'SizeNESW':-45}[role]
            small=small.rotate(angle,resample=Image.Resampling.BICUBIC,center=(32*scale,32*scale))
            image=Image.new('RGBA',(128*scale,128*scale));image.alpha_composite(small,(0,0))
    elif role == 'SizeAll':
        polygon([(32,3),(19,17),(26,17),(26,26),(17,26),(17,19),(3,32),(17,45),(17,38),
                 (26,38),(26,47),(19,47),(32,61),(45,47),(38,47),(38,38),(47,38),(47,45),
                 (61,32),(47,19),(47,26),(38,26),(38,17),(45,17)])
    elif role == 'Hand':
        polygon([(26,34),(26,11),(28,5),(35,4),(40,9),(40,29),(46,25),(53,29),(59,28),
                 (66,33),(67,52),(62,68),(35,68),(22,56),(7,43),(9,36),(16,34),(26,43)])
        hot=(33,5)
    elif role == 'Person':
        d.ellipse((20,4,44,28),fill=accent,outline=ink,width=2)
        d.rounded_rectangle((9,32,56,65),radius=16,fill=accent,outline=ink,width=2)
        hot=(32,16)
    elif role == 'Pin':
        polygon([(32,65),(11,31),(12,16),(22,6),(41,6),(52,16),(53,31)])
        d.ellipse((24,17,40,33),fill=pale,outline=ink,width=2)
        hot=(32,62)
    return image.resize((128,128),Image.Resampling.LANCZOS), hot


def compile_cursor(pose, role, accent, pale):
    canvas=Image.new('RGBA',(128,128))
    figure=fit_character(pose,(88,96))
    canvas.alpha_composite(figure,(38+(88-figure.width)//2,126-figure.height))
    glyph,hot=functional_cursor(role,accent,pale)
    canvas.alpha_composite(glyph)
    return canvas,hot


def write_cur(path, image, hotspot):
    stream=io.BytesIO()
    image.save(stream,format='ICO',sizes=[(n,n) for n in SIZES],bitmap_format='bmp')
    raw=bytearray(stream.getvalue())
    struct.pack_into('<H',raw,2,2)
    count=struct.unpack_from('<H',raw,4)[0]
    entries=[]
    for index in range(count):
        offset=6+16*index
        size=raw[offset] or 256
        hot=tuple(max(0,min(size-1,round(value*size/128))) for value in hotspot)
        struct.pack_into('<HH',raw,offset+4,*hot)
        entries.append({'size':size,'hotspot':hot})
    path.write_bytes(raw)
    return entries


def compile_icon(pose, symbol, accent, pale):
    canvas=Image.new('RGBA',(256,256))
    character=fit_character(pose,(230,236))
    canvas.alpha_composite(character,((250-character.width)//2,3))
    badge=base.icon(symbol,accent,pale).resize((88,88),Image.Resampling.LANCZOS)
    canvas.alpha_composite(badge,(167,167))
    return canvas


def contact_sheet(folder, name, icons, cursors):
    canvas=Image.new('RGB',(1440,1010),'#f6f8fb')
    d=ImageDraw.Draw(canvas)
    title=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',32)
    label=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
    d.text((28,18),name+' · 角色图标与鼠标指针',font=title,fill='#273445')
    d.text((28,70),'12 款角色图标 · 17 种指针状态 · 每种指针独立点击位置',font=label,fill='#6d7a8b')
    for i,image in enumerate(icons):
        x=24+(i%12)*118;y=116
        d.rounded_rectangle((x,y,x+110,y+155),radius=12,fill='white',outline='#e2e7ee')
        image=image.resize((100,100),Image.Resampling.LANCZOS)
        canvas.paste(image,(x+5,y+9),image)
        d.text((x+10,y+125),ICON_LABELS[i],font=label,fill='#36475b')
    for i,image in enumerate(cursors):
        x=24+(i%6)*236;y=300+(i//6)*228
        d.rounded_rectangle((x,y,x+224,y+212),radius=14,fill='white',outline='#e2e7ee')
        image=image.resize((128,128),Image.Resampling.LANCZOS)
        canvas.paste(image,(x+48,y+10),image)
        d.text((x+16,y+155),ROLE_LABELS[i],font=label,fill='#36475b')
        d.text((x+16,y+181),base.ROLES[i],font=small,fill='#8794a5')
    canvas.save(folder/'accessories-preview.png',optimize=True)


def build():
    catalog_path=ROOT/'assets/templates/catalog.json'
    catalog=json.loads(catalog_path.read_text(encoding='utf-8-sig'))
    manifests=[]
    for ident,name,subtitle,accent,pale,motif in base.THEMES:
        art=ROOT/'assets/character-art'/ident/'atlas.png'
        figures=sprites(art)
        folder=ROOT/'assets/templates'/ident
        preview_dir=folder/'cursor-previews'
        preview_dir.mkdir(exist_ok=True)
        icon_images=[];cursor_images=[];entries={}
        for index,symbol in enumerate(base.ICON_MATCHES):
            image=compile_icon(figures[POSE_FOR_ICON[index]],symbol,accent,pale)
            image.save(folder/'icons'/f'{symbol}.ico',sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
            icon_images.append(image)
        for index,role in enumerate(base.ROLES):
            image,hot=compile_cursor(figures[POSE_FOR_ROLE[index]],role,accent,pale)
            entries[role]=write_cur(folder/'cursors'/f'{role}.cur',image,hot)
            image.save(preview_dir/f'{role}.png',optimize=True)
            if role=='Arrow':image.save(folder/'cursor-preview.png',optimize=True)
            cursor_images.append(image)
        contact_sheet(folder,name,icon_images,cursor_images)
        item=next(item for item in catalog if item['id']==ident)
        item.update(cursorSize=64,assetStyle='character-functional-v2',version='2.0.0',
                    artwork='AI 生成同人插画与角色图标；指针布局参考本机原厂角色加功能符号；作品及角色名称属于各自权利人')
        manifests.append({'id':ident,'icons':12,'cursorRoles':17,'atlas':str(art.relative_to(ROOT)),'cursorEntries':entries})
    catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target=ROOT/'docs/development/0.5.0-asset-manifest.json'
    target.write_text(json.dumps(manifests,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Compiled 10 character packs, 120 icons, 170 multi-resolution cursors and full previews.')


if __name__=='__main__':
    build()
