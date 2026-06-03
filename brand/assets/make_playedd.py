#!/usr/bin/env python3
"""Generate PLAYEDD channel art in the crude doodle style."""
import math, random
from PIL import Image, ImageDraw, ImageFont

random.seed(11)
FONTS = "/home/claude/assets/fonts"
OUT = "/home/claude/assets_playedd"

PAPER = (250, 249, 244); INK = (26, 26, 26); RED = (201, 48, 32)
TAN = (228, 198, 138)

def marker(sz): return ImageFont.truetype(f"{FONTS}/PermanentMarker.ttf", sz)
def hand(sz):   return ImageFont.truetype(f"{FONTS}/PatrickHand.ttf", sz)

def wline(d, p0, p1, width=8, fill=INK, jitter=3, segs=14):
    (x0,y0),(x1,y1)=p0,p1; pts=[]
    for i in range(segs+1):
        t=i/segs
        pts.append((x0+(x1-x0)*t+random.uniform(-jitter,jitter), y0+(y1-y0)*t+random.uniform(-jitter,jitter)))
    d.line(pts, fill=fill, width=width, joint="curve")

def wrect(d, box, width=7, fill=INK, jitter=3):
    x0,y0,x1,y1=box
    wline(d,(x0,y0),(x1,y0),width,fill,jitter); wline(d,(x1,y0),(x1,y1),width,fill,jitter)
    wline(d,(x1,y1),(x0,y1),width,fill,jitter); wline(d,(x0,y1),(x0,y0),width,fill,jitter)

def wcircle(d, cx, cy, r, width=8, fill=INK, jitter=3, segs=40):
    pts=[]; start=random.uniform(0,0.3)
    for i in range(segs+1):
        a=start+2*math.pi*i/segs; rr=r+random.uniform(-jitter,jitter)
        pts.append((cx+rr*math.cos(a), cy+rr*math.sin(a)))
    d.line(pts, fill=fill, width=width, joint="curve")

def stamp(text, font, angle=-10, color=RED):
    tmp=Image.new("RGBA",(1000,300),(0,0,0,0)); td=ImageDraw.Draw(tmp)
    bb=td.textbbox((0,0),text,font=font); tw,th=bb[2]-bb[0],bb[3]-bb[1]; pad=28
    bw,bh=tw+pad*2,th+pad*2
    box=Image.new("RGBA",(bw+20,bh+20),(0,0,0,0)); bd=ImageDraw.Draw(box)
    wrect(bd,(10,10,10+bw,10+bh),width=8,fill=color,jitter=4)
    bd.text((10+pad-bb[0],10+pad-bb[1]),text,font=font,fill=color)
    return box.rotate(angle, expand=True, resample=Image.BICUBIC)

def face(d, cx, cy, r, mood="dismay"):
    wcircle(d,cx,cy,r,width=max(6,r//12))
    ex=r*0.34
    d.ellipse((cx-ex-9,cy-r*0.28,cx-ex+9,cy-r*0.28+18),fill=INK)
    d.ellipse((cx+ex-9,cy-r*0.28,cx+ex+9,cy-r*0.28+18),fill=INK)
    if mood=="dismay":
        wline(d,(cx-r*0.28,cy+r*0.42),(cx+r*0.28,cy+r*0.42),width=max(4,r//18),jitter=2,segs=6)
    else:
        wline(d,(cx-r*0.25,cy+r*0.3),(cx+r*0.25,cy+r*0.4),width=max(4,r//18),jitter=2,segs=6)

# AVATAR 800 — stickman who just got PLAYED (red stamp across face)
def make_avatar():
    S=800; img=Image.new("RGB",(S,S),PAPER); d=ImageDraw.Draw(img)
    cx,cy=S//2,S//2-30
    face(d,cx,cy,235,mood="dismay")
    st=stamp("PLAYEDD",marker(80),angle=-11)
    if st.width>620: st=st.resize((620,int(st.height*620/st.width)),Image.BICUBIC)
    img.paste(st,(cx-st.width//2,cy-st.height//2+10),st)
    img.save(f"{OUT}/avatar_800.png")

# BANNER 2560x1440, safe area centered 1546x423
def make_banner():
    W,H=2560,1440; img=Image.new("RGB",(W,H),PAPER); d=ImageDraw.Draw(img)
    cx=W//2
    for gx in range(0,W,60): d.line([(gx,0),(gx,H)],fill=(238,237,230),width=1)
    # folder + GOTCHA stamp, top-left
    fx,fy=230,150
    d.polygon([(fx,fy+40),(fx+60,fy+40),(fx+90,fy+10),(fx+250,fy+10),(fx+250,fy+220),(fx,fy+220)],fill=TAN)
    wrect(d,(fx,fy+40,fx+250,fy+220),width=6); wline(d,(fx+60,fy+40),(fx+90,fy+10),width=6); wline(d,(fx+90,fy+10),(fx+250,fy+10),width=6)
    g=stamp("GOTCHA",marker(34),angle=-9); img.paste(g,(fx+40,fy+95),g)
    # marionette stickman bottom-left (being played)
    sx,sy=360,1090
    # strings from top
    wline(d,(sx-60,820),(sx-60,sy+40),width=3,jitter=1); wline(d,(sx+60,820),(sx+60,sy+40),width=3,jitter=1)
    face(d,sx,sy,70,mood="dismay")
    wline(d,(sx,sy+70),(sx,sy+200),width=12)
    wline(d,(sx,sy+110),(sx-60,sy+40),width=10); wline(d,(sx,sy+110),(sx+60,sy+40),width=10)  # arms up to strings
    wline(d,(sx,sy+200),(sx-60,sy+300),width=10); wline(d,(sx,sy+200),(sx+60,sy+300),width=10)
    # question marks + redacted bars right side
    d.text((2060,150),"?",font=marker(150),fill=RED); d.text((2260,330),"?",font=marker(85),fill=INK)
    d.rectangle((2060,1150,2390,1192),fill=INK); d.rectangle((2130,1235,2340,1272),fill=INK)
    # red arrow under title
    wline(d,(cx-470,1050),(cx-340,975),width=10,fill=RED); wline(d,(cx-340,975),(cx-372,1005),width=10,fill=RED); wline(d,(cx-340,975),(cx-308,1007),width=10,fill=RED)
    # WORDMARK
    tf=marker(190); word="PLAYEDD"
    b=d.textbbox((0,0),word,font=tf); w=b[2]-b[0]
    y=540
    d.text((cx-w//2,y),word,font=tf,fill=INK)
    # wobbly underline
    wline(d,(cx-w//2,y+225),(cx+w//2,y+218),width=9,fill=RED,jitter=4)
    # tagline
    sf=hand(74); tag="you're being played. here's how."
    bt=d.textbbox((0,0),tag,font=sf); wt=bt[2]-bt[0]
    d.text((cx-wt//2,y+250),tag,font=sf,fill=(70,70,70))
    img.save(f"{OUT}/banner_2560x1440.png")

def make_watermark():
    S=150; img=Image.new("RGBA",(S,S),(0,0,0,0)); d=ImageDraw.Draw(img)
    face(d,S//2,S//2,55,mood="dismay")
    img.save(f"{OUT}/watermark_150.png")

def make_thumb():
    W,Hh=1280,720; img=Image.new("RGB",(W,Hh),PAPER); d=ImageDraw.Draw(img)
    wrect(d,(20,20,W-20,Hh-20),width=8)
    d.text((60,70),"BIG HOOK TEXT",font=marker(96),fill=INK)
    d.text((60,190),"(2-5 punchy words)",font=hand(44),fill=(120,120,120))
    wrect(d,(760,300,1180,660),width=6,jitter=4); d.text((800,300),"doodle here",font=hand(40),fill=(150,150,150))
    s=stamp("PLAYEDD",marker(34),angle=-9); img.paste(s,(60,560),s)
    img.save(f"{OUT}/thumbnail_template_1280x720.png")

import os; os.makedirs(OUT,exist_ok=True)
make_avatar(); make_banner(); make_watermark(); make_thumb()
print("playedd assets done")
