"""Render loopable wallpaper videos from the bundled artwork using FFmpeg.

This is a build-time tool only; the installed app plays the resulting H.264 files
with WebView2 and does not require FFmpeg or Python.
"""
from pathlib import Path
import hashlib
import json
import math
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'templates'
DURATION, FPS = 12, 24


def render(pack):
    source = ASSETS / pack['wallpaper']
    target = source.with_name('wallpaper-motion.mp4')
    rng = random.Random(pack['id'])
    frames = DURATION * FPS
    filters = [
        "[0:v]scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,"
        f"zoompan=z='1.04+0.012*sin(2*PI*on/{frames})':"
        f"x='(iw-iw/zoom)/2+14*sin(2*PI*on/{frames})':"
        f"y='(ih-ih/zoom)/2+8*cos(2*PI*on/{frames})':"
        f"d={frames}:s=1920x1080:fps={FPS},format=yuv420p[base]",
        f"color=c=0x{pack['pale'][1:]}:s=24x24:r={FPS}:d={DURATION},format=rgba,"
        "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
        "a='85*exp(-(pow(X-12,2)+pow(Y-12,2))/24)',split=12" + ''.join(f'[p{i}]' for i in range(12)),
    ]
    last = 'base'
    for i in range(12):
        x, y = rng.randint(100, 1800), rng.randint(70, 980)
        phase = rng.random() * math.tau
        label = f'v{i}'
        filters.append(f"[{last}][p{i}]overlay=x='{x}+45*sin(2*PI*t/{DURATION}+{phase:.4f})':"
                       f"y='{y}+30*cos(2*PI*t/{DURATION}+{phase:.4f})':shortest=1[{label}]")
        last = label
    args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
            '-filter_complex_threads', '2', '-filter_complex', ';'.join(filters), '-map', f'[{last}]',
            '-t', str(DURATION), '-an', '-c:v', 'libx264', '-threads', '4', '-preset', 'fast',
            '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)]
    subprocess.run(args, check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                               '-show_format', '-of', 'json', str(target)]))
    video = probe['streams'][0]
    assert video['codec_name'] == 'h264' and video['width'] == 1920 and video['height'] == 1080
    assert int(video['nb_frames']) == frames
    # Decode separated frames to establish that the shipped clip actually changes.
    hashes = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(target), '-vf',
                                     r'select=eq(n\,0)+eq(n\,144)', '-fps_mode', 'passthrough',
                                     '-f', 'framemd5', '-']).decode()
    values = [line.rsplit(',', 1)[-1].strip() for line in hashes.splitlines() if not line.startswith('#')]
    assert len(set(values)) == 2, 'Video must contain motion'
    pack.update(animatedWallpaper=f"{pack['id']}/wallpaper-motion.mp4",
                motionLabel='缓慢运镜 · 柔光漂浮', motionDuration=DURATION)
    print(f"{pack['id']}: {target.stat().st_size} bytes, {frames} frames", flush=True)
    return {'id': pack['id'], 'source': pack['wallpaper'], 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'output': pack['animatedWallpaper'], 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'bytes': target.stat().st_size, 'width': 1920, 'height': 1080, 'frames': frames, 'fps': FPS,
            'duration': DURATION, 'distinctFrameHashes': values, 'method': 'Periodic camera drift and procedural soft-light particles; original artwork retained.'}


if __name__ == '__main__':
    catalog = json.loads((ASSETS / 'catalog.json').read_text(encoding='utf-8'))
    evidence = [render(pack) for pack in catalog]
    (ASSETS / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'assets' / 'motion-provenance.json').write_text(json.dumps({
        'generator': 'tools/build-motion-wallpapers.py', 'clips': evidence,
        'notes': 'Derived ambient motion, not character animation. Silent seamless periodic trajectories.'
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
