"""Build compact, editable native icon/cursor assets. Wallpaper art is imagegen output."""
from pathlib import Path
import io, json, math, struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
THEMES = [
 ('wuthering-waves','鸣潮','今汐 · 云海听潮','#377f84','#d9f3ed','jade'),
 ('punishing-gray-raven','战双帕弥什','露西亚 · 绯色黎明','#be3d58','#ffd5db','crimson'),
 ('genshin-impact','原神','旅行者 · 风起之地','#3d99b9','#e4f8ec','sky'),
 ('identity-v','第五人格','园丁 · 月下庄园','#786399','#efe3fa','gothic'),
 ('milk-mocha-dogs','线条小狗','小狗 · 奶油野餐','#bc8a58','#fff1d9','cream'),
 ('honkai-star-rail','崩坏：星穹铁道','三月七 · 星河列车','#9b6dba','#f3ddff','galaxy'),
 ('zenless-zone-zero','绝区零','妮可 · 新艾利都','#cf7149','#fff0d5','urban'),
 ('arknights','明日方舟','阿米娅 · 破晓之城','#337d9d','#d3f3fa','rhodes'),
 ('blue-archive','蔚蓝档案','阿洛娜 · 晴空海岸','#419dcc','#e4f9ff','blue'),
 ('chiikawa','Chiikawa','吉伊卡哇 · 软糖草地','#b885a1','#ffedf5','pastel'),
]
ROLES = ['Arrow','Help','AppStarting','Wait','Crosshair','IBeam','NWPen','No','SizeNS','SizeWE','SizeNWSE','SizeNESW','SizeAll','UpArrow','Hand','Person','Pin']
ICON_MATCHES = {
 'folder':['文件','资源管理','explorer','folder'], 'browser':['chrome','edge','firefox','浏览器'],
 'chat':['微信','wechat','qq','聊天','腾讯会议'], 'notes':['notepad','notion','obsidian','记事','笔记'],
 'code':['codex','code','编程','deepseek'], 'science':['comsol','vasp','origin','matlab','科研','计算'],
 'books':['zotero','calibre','文献','论文'], 'music':['音乐','music','spotify'],
 'cloud':['网盘','cloud','onedrive'], 'games':['steam','游戏','原神','鸣潮','战双','绝区','星穹'],
 'office':['word','excel','powerpoint','wps'], 'tools':['工具','everything','bandizip','geek'],
}

def icon(symbol, accent, pale):
    image=Image.new('RGBA',(256,256)); d=ImageDraw.Draw(image)
    d.rounded_rectangle((9,9,247,247),radius=64,fill=accent)
    d.rounded_rectangle((18,18,238,238),radius=57,outline=pale,width=3)
    ink=pale; w=12
    if symbol=='folder':
        d.rounded_rectangle((49,67,135,105),radius=13,fill=ink);d.rounded_rectangle((43,90,216,188),radius=17,fill=ink)
    elif symbol=='browser':
        d.ellipse((55,55,201,201),outline=ink,width=w);d.ellipse((94,55,162,201),outline=ink,width=8);d.line((58,128,198,128),fill=ink,width=8)
    elif symbol=='chat':
        d.rounded_rectangle((44,62,210,176),radius=35,fill=ink);d.polygon([(67,160),(63,204),(109,169)],fill=ink)
        for x in (87,127,167):d.ellipse((x-7,112,x+7,126),fill=accent)
    elif symbol=='notes':
        d.rounded_rectangle((65,45,196,210),radius=17,fill=ink)
        for y in (88,122,156):d.line((88,y,171,y),fill=accent,width=10)
    elif symbol=='code':
        d.line([(92,80),(44,128),(92,174)],fill=ink,width=w);d.line([(164,80),(212,128),(164,174)],fill=ink,width=w);d.line((145,61,115,194),fill=ink,width=w)
    elif symbol=='science':
        for angle in (0,60,120):
            layer=Image.new('RGBA',(256,256));ld=ImageDraw.Draw(layer);ld.ellipse((38,94,218,162),outline=ink,width=8);image.alpha_composite(layer.rotate(angle))
        ImageDraw.Draw(image).ellipse((113,113,143,143),fill=ink)
    elif symbol=='books':
        d.rounded_rectangle((47,58,119,195),radius=10,fill=ink);d.rounded_rectangle((137,58,209,195),radius=10,fill=ink);d.line((128,66,128,200),fill=ink,width=7)
    elif symbol=='music':
        d.line((107,176,107,67,187,50,187,151),fill=ink,width=14);d.ellipse((63,160,112,198),fill=ink);d.ellipse((143,138,192,176),fill=ink)
    elif symbol=='cloud':
        d.ellipse((56,105,140,188),fill=ink);d.ellipse((85,66,181,178),fill=ink);d.ellipse((139,104,209,188),fill=ink);d.rectangle((88,127,178,186),fill=ink)
    elif symbol=='games':
        d.rounded_rectangle((40,86,216,181),radius=32,fill=ink);d.line((70,132,108,132),fill=accent,width=10);d.line((89,113,89,151),fill=accent,width=10)
        for x,y in ((162,119),(187,140)):d.ellipse((x-8,y-8,x+8,y+8),fill=accent)
    elif symbol=='office':
        d.rounded_rectangle((66,43,197,209),radius=15,fill=ink)
        for x,y in ((90,157),(119,126),(148,93)):d.rounded_rectangle((x,y,x+18,180),radius=4,fill=accent)
    else:
        for x,y in ((67,67),(151,67),(67,151),(151,151)):d.rounded_rectangle((x,y,x+40,y+40),radius=12,fill=ink)
    return image

def cursor(role, accent, pale):
    # Work at 4x, then downsample for a clean 48px pointer. Hotspots are explicit.
    image=Image.new('RGBA',(192,192));d=ImageDraw.Draw(image);c=accent;o='#20283b';w=7;hot=(24,24)
    if role in ('Arrow','Help','AppStarting','Person','Pin'):
        d.polygon([(20,12),(20,145),(57,110),(88,166),(111,152),(80,98),(131,96)],fill=pale,outline=o,width=w);hot=(5,3)
        if role!='Arrow':
            d.ellipse((109,112,186,189),fill=c,outline=pale,width=5)
            if role=='Help': d.arc((130,126,164,152),180,450,fill=pale,width=6);d.ellipse((145,164,151,170),fill=pale)
            elif role=='AppStarting':d.arc((126,129,170,174),0,275,fill=pale,width=7)
            elif role=='Person':d.ellipse((137,126,157,146),fill=pale);d.rounded_rectangle((126,153,168,175),radius=9,fill=pale)
            else:d.ellipse((135,126,158,150),outline=pale,width=5);d.polygon([(135,144),(158,144),(147,174)],fill=pale)
    elif role=='IBeam':
        d.line((96,26,96,166),fill=o,width=16);d.line((96,26,96,166),fill=pale,width=8)
        for y in (24,167):d.line((68,y,124,y),fill=o,width=14);d.line((68,y,124,y),fill=pale,width=6)
    elif role in ('Crosshair','SizeAll'):
        for points in [[(96,17),(96,174)],[(17,96),(174,96)]]:d.line(points,fill=o,width=13);d.line(points,fill=pale,width=6)
        if role=='SizeAll':
            for a in (0,90,180,270):
                p=[(96,8),(75,38),(117,38)];r=Image.new('RGBA',image.size);ImageDraw.Draw(r).polygon(p,fill=pale,outline=o,width=4);image.alpha_composite(r.rotate(a))
    elif role.startswith('Size') or role=='UpArrow':
        d.polygon([(96,16),(59,59),(81,59),(81,134),(59,134),(96,178),(133,134),(111,134),(111,59),(133,59)],fill=pale,outline=o,width=6)
        angle={'SizeWE':90,'SizeNWSE':45,'SizeNESW':-45}.get(role,0);image=image.rotate(angle)
    elif role=='Wait':
        d.ellipse((30,30,163,163),outline=o,width=22);d.arc((30,30,163,163),-90,180,fill=c,width=15);d.arc((30,30,163,163),185,265,fill=pale,width=15)
    elif role=='No':
        d.ellipse((28,28,164,164),fill=pale,outline=o,width=7);d.ellipse((45,45,148,148),outline=c,width=17);d.line((58,58,134,134),fill=c,width=16)
    elif role=='Hand':
        d.rounded_rectangle((77,15,102,132),radius=12,fill=pale,outline=o,width=5);d.rounded_rectangle((70,90,166,178),radius=25,fill=pale,outline=o,width=5);d.polygon([(72,132),(31,103),(25,122),(77,176),(115,175)],fill=pale,outline=o,width=5);hot=(23,4)
    else:
        d.polygon([(122,21),(159,47),(66,168),(30,180),(40,139)],fill=pale,outline=o,width=7);d.line((60,139,134,43),fill=c,width=10);hot=(8,44)
    return image.resize((48,48),Image.Resampling.LANCZOS),hot

def brand():
    folder=ASSETS/'brand';folder.mkdir(parents=True,exist_ok=True)
    image=Image.new('RGBA',(1024,1024));pixels=image.load()
    for y in range(1024):
        for x in range(1024):
            t=(x+y)/2046;pixels[x,y]=(int(99-49*t),int(71+68*t),int(215+28*t),255)
    mask=Image.new('L',image.size);ImageDraw.Draw(mask).rounded_rectangle((45,45,979,979),radius=230,fill=255);image.putalpha(mask)
    d=ImageDraw.Draw(image)
    d.rounded_rectangle((192,228,717,740),radius=93,fill='#a9daed')
    d.rounded_rectangle((290,324,832,824),radius=94,fill='#fbfbff')
    d.rounded_rectangle((342,384,780,679),radius=49,fill='#7769d5')
    d.polygon([(371,631),(485,508),(572,590),(643,541),(752,650)],fill='#dbeafc')
    d.ellipse((666,426,722,482),fill='#fff4c9')
    d.rounded_rectangle((491,731,632,752),radius=10,fill='#aaa1df')
    d.polygon([(784,138),(811,211),(884,238),(811,265),(784,338),(757,265),(684,238),(757,211)],fill='#fff2ca')
    image.save(folder/'theme-studio.png',optimize=True)
    image.save(folder/'theme-studio.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    (folder/'theme-studio.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#6347d7"/><stop offset="1" stop-color="#328bf3"/></linearGradient></defs><rect x="45" y="45" width="934" height="934" rx="230" fill="url(#g)"/><rect x="192" y="228" width="525" height="512" rx="93" fill="#a9daed"/><rect x="290" y="324" width="542" height="500" rx="94" fill="#fbfbff"/><rect x="342" y="384" width="438" height="295" rx="49" fill="#7769d5"/><path d="M371 631L485 508L572 590L643 541L752 650Z" fill="#dbeafc"/><circle cx="694" cy="454" r="28" fill="#fff4c9"/><rect x="491" y="731" width="141" height="21" rx="10" fill="#aaa1df"/><path d="M784 138L811 211L884 238L811 265L784 338L757 265L684 238L757 211Z" fill="#fff2ca"/></svg>''',encoding='utf-8')

def build():
    brand();catalog=[]
    for ident,name,subtitle,accent,pale,motif in THEMES:
        folder=ASSETS/'templates'/ident
        (folder/'icons').mkdir(parents=True,exist_ok=True);(folder/'cursors').mkdir(exist_ok=True)
        for symbol in ICON_MATCHES:
            icon(symbol,accent,pale).save(folder/'icons'/f'{symbol}.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
        for role in ROLES:
            image,hot=cursor(role,accent,pale);stream=io.BytesIO();image.save(stream,format='ICO',sizes=[(48,48)],bitmap_format='bmp')
            if role == 'Arrow': image.save(folder/'cursor-preview.png')
            raw=bytearray(stream.getvalue());struct.pack_into('<H',raw,2,2);struct.pack_into('<HH',raw,10,*hot);(folder/'cursors'/f'{role}.cur').write_bytes(raw)
        item={'id':ident,'name':name,'subtitle':subtitle,'accent':accent,'pale':pale,'wallpaper':f'{ident}/wallpaper.jpg','thumbnail':f'{ident}/thumbnail.webp','cursorSize':48,'iconMatches':ICON_MATCHES,'artwork':'AI 生成同人插画；作品及角色名称属于各自权利人'}
        item.update(animatedWallpaper=f'{ident}/wallpaper-motion.mp4',motionLabel='缓慢运镜 · 柔光漂浮',motionDuration=12)
        catalog.append(item)
    (ASSETS/'templates'/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(catalog)} packs, {len(ROLES)} cursor roles and {len(ICON_MATCHES)} icons each.')

if __name__=='__main__':build()
