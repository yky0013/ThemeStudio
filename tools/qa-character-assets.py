"""Validate every encoded cursor using Windows, including all size/hotspot pairs."""
from pathlib import Path
import ctypes
from ctypes import wintypes as wt
import hashlib
import json
import struct
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'components/icon-workbench'))
import cursor_adapter as ca
from native_icons import cursor_image

class IconInfo(ctypes.Structure):
    _fields_=[('fIcon',wt.BOOL),('xHotspot',wt.DWORD),('yHotspot',wt.DWORD),('hbmMask',wt.HBITMAP),('hbmColor',wt.HBITMAP)]

user32=ctypes.WinDLL('user32',use_last_error=True)
gdi32=ctypes.WinDLL('gdi32',use_last_error=True)
user32.LoadImageW.argtypes=[wt.HINSTANCE,wt.LPCWSTR,wt.UINT,ctypes.c_int,ctypes.c_int,wt.UINT]
user32.LoadImageW.restype=wt.HANDLE
user32.GetIconInfo.argtypes=[wt.HANDLE,ctypes.POINTER(IconInfo)]
user32.GetIconInfo.restype=wt.BOOL
user32.DestroyCursor.argtypes=[wt.HANDLE]
gdi32.DeleteObject.argtypes=[wt.HGDIOBJ]

def main():
    catalog=json.loads((ROOT/'assets/templates/catalog.json').read_text(encoding='utf-8-sig'))
    assert len(catalog)==7
    before=ca.snapshot()
    result={'packs':[],'icons':0,'cursors':0,'nativeCursorLoads':0,'hotspotsVerified':0}
    overview=Image.new('RGB',(1400,1660),'#f5f7fb')
    d=ImageDraw.Draw(overview)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
    d.text((24,16),'Theme Studio 0.5.0 · 7 套角色图标与鼠标',font=font,fill='#293746')
    for index,item in enumerate(catalog):
        folder=ROOT/'assets/templates'/item['id']
        assert item['version']=='2.0.0' and item['cursorSize']==64
        assert (folder/'accessories-preview.png').is_file()
        hashes=set()
        for file in (folder/'icons').glob('*.ico'):
            with Image.open(file) as icon:
                assert icon.ico.sizes()=={(n,n) for n in (16,24,32,48,64,128,256)}
                assert icon.ico.getimage((256,256)).getchannel('A').getextrema()==(0,255)
            result['icons']+=1
        files=list((folder/'cursors').glob('*.cur'))
        assert len(files)==17
        for file in files:
            data=file.read_bytes()
            assert struct.unpack_from('<HH',data)==(0,2)
            count=struct.unpack_from('<H',data,4)[0]
            assert count==4
            seen=set()
            for entry in range(count):
                w,h,colors,res,x,y,length,offset=struct.unpack_from('<BBBBHHII',data,6+entry*16)
                w=w or 256;h=h or 256
                assert w==h and w in (32,48,64,96)
                assert 0<=x<w and 0<=y<h and offset+length<=len(data)
                handle=user32.LoadImageW(None,str(file),2,w,h,0x10)
                if not handle:raise ctypes.WinError(ctypes.get_last_error())
                info=IconInfo()
                try:
                    if not user32.GetIconInfo(handle,ctypes.byref(info)):raise ctypes.WinError(ctypes.get_last_error())
                    assert not info.fIcon and (info.xHotspot,info.yHotspot)==(x,y), (file,w,x,y,info.xHotspot,info.yHotspot)
                finally:
                    if info.hbmMask:gdi32.DeleteObject(info.hbmMask)
                    if info.hbmColor:gdi32.DeleteObject(info.hbmColor)
                    user32.DestroyCursor(handle)
                result['nativeCursorLoads']+=1;result['hotspotsVerified']+=1;seen.add(w)
            assert seen=={32,48,64,96}
            hashes.add(hashlib.sha256(data).hexdigest())
            result['cursors']+=1
        assert len(hashes)==17, 'Cursor states must be visually distinct'
        result['packs'].append({'id':item['id'],'icons':12,'cursors':17,'sizes':[32,48,64,96]})
        x=24+(index%2)*696;y=70+(index//2)*314
        d.rounded_rectangle((x,y,x+672,y+292),radius=16,fill='white',outline='#dbe2ec')
        d.text((x+18,y+13),item['name'],font=font,fill='#293746')
        for j,symbol in enumerate(['folder','chat','science','music']):
            with Image.open(folder/'icons'/f'{symbol}.ico') as image:
                image=image.ico.getimage((128,128)).convert('RGBA').resize((96,96),Image.Resampling.LANCZOS)
            overview.paste(image,(x+18+j*114,y+55),image)
        for j,role in enumerate(['Arrow','Help','IBeam','Hand']):
            image=cursor_image(str(folder/'cursors'/f'{role}.cur'),96)
            overview.paste(image,(x+20+j*114,y+175),image if image.mode=='RGBA' else None)
    assert result['icons']==120 and result['cursors']==170 and result['nativeCursorLoads']==680
    assert ca.snapshot()==before
    result.update(passed=True,systemCursorsUnchanged=True)
    out=ROOT/'qa/character-assets';out.mkdir(parents=True,exist_ok=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    overview.save(out/'overview.png',optimize=True)
    print(json.dumps({key:value for key,value in result.items() if key!='packs'}))

if __name__=='__main__':main()
