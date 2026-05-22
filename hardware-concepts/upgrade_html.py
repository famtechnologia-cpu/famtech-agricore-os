#!/usr/bin/env python3
"""
Famtech AgriCore HTML Upgrade
  1. Better model-viewer rendering (environment-image, camera-orbit, exposure)
  2. Interactive part-annotation hotspot buttons on every model-viewer
  3. 2D technical SVG drawing panel (Front / Side / Top) below the 3D viewer
  4. Hotspot + 2D-view CSS injected into each page
"""
import re, os

BASE = "/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts"

# ─── SVG renderer ────────────────────────────────────────────────────────────
FB  = "rgba(18,56,130,0.22)"    # body fill
FD  = "rgba(8,20,60,0.55)"     # dark fill
FP  = "rgba(30,100,200,0.18)"  # part fill
FA  = "rgba(0,180,100,0.20)"   # accent fill
SM  = "#2a7ad9"                 # main stroke
SP  = "#1a5aaa"                 # part stroke
SA  = "#00cc88"                 # accent stroke
SW  = "#ff8c00"                 # warning/callout
TD  = "#3a6aaa"                 # dim text
TL  = "#7aaadd"                 # label text

def _f(v): return f"{v:.1f}"

def _shapes_svg(shapes, vw=260, vh=192):
    out = [
        f'<svg viewBox="0 0 {vw} {vh}" xmlns="http://www.w3.org/2000/svg">',
        '<defs><pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse">'
        '<path d="M20,0L0,0L0,20" fill="none" stroke="#0d1a38" stroke-width=".6"/>'
        '</pattern></defs>',
        f'<rect width="{vw}" height="{vh}" fill="#060c1b"/>',
        f'<rect width="{vw}" height="{vh}" fill="url(#g)"/>',
    ]
    for s in shapes:
        t = s[0]
        if t == 'r':    # rect: x,y,w,h [fill,stroke,sw]
            x,y,w,h = s[1],s[2],s[3],s[4]
            f,st,sw = (s[5] if len(s)>5 else FB),(s[6] if len(s)>6 else SM),(s[7] if len(s)>7 else 1.2)
            out.append(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" fill="{f}" stroke="{st}" stroke-width="{sw}" rx="1"/>')
        elif t == 'rr': # rounded rect: x,y,w,h,rx [fill,stroke]
            x,y,w,h,rx = s[1],s[2],s[3],s[4],s[5]
            f,st = (s[6] if len(s)>6 else FB),(s[7] if len(s)>7 else SM)
            out.append(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{rx}" fill="{f}" stroke="{st}" stroke-width="1.2"/>')
        elif t == 'c':  # circle: cx,cy,r [fill,stroke]
            cx,cy,r = s[1],s[2],s[3]
            f,st = (s[4] if len(s)>4 else FB),(s[5] if len(s)>5 else SM)
            out.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" fill="{f}" stroke="{st}" stroke-width="1.2"/>')
        elif t == 'e':  # ellipse: cx,cy,rx,ry [fill,stroke]
            cx,cy,rx,ry = s[1],s[2],s[3],s[4]
            f,st = (s[5] if len(s)>5 else FB),(s[6] if len(s)>6 else SM)
            out.append(f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(rx)}" ry="{_f(ry)}" fill="{f}" stroke="{st}" stroke-width="1.2"/>')
        elif t == 'l':  # line: x1,y1,x2,y2 [stroke,sw,dash]
            x1,y1,x2,y2 = s[1],s[2],s[3],s[4]
            st,sw,da = (s[5] if len(s)>5 else SP),(s[6] if len(s)>6 else 0.8),(s[7] if len(s)>7 else "")
            da_attr = f' stroke-dasharray="{da}"' if da else ""
            out.append(f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" stroke="{st}" stroke-width="{sw}"{da_attr}/>')
        elif t == 'p':  # polygon: [(x,y),...] [fill,stroke]
            pts = s[1]; f,st = (s[2] if len(s)>2 else FB),(s[3] if len(s)>3 else SM)
            ps = " ".join(f"{_f(x)},{_f(y)}" for x,y in pts)
            out.append(f'<polygon points="{ps}" fill="{f}" stroke="{st}" stroke-width="1.2"/>')
        elif t == 'pa': # path: d [fill,stroke,sw]
            d = s[1]; f,st,sw = (s[2] if len(s)>2 else 'none'),(s[3] if len(s)>3 else SM),(s[4] if len(s)>4 else 1.2)
            out.append(f'<path d="{d}" fill="{f}" stroke="{st}" stroke-width="{sw}"/>')
        elif t == 'tx': # text: x,y,text [size,color,anchor]
            x,y,txt = s[1],s[2],s[3]
            sz,col,anc = (s[4] if len(s)>4 else 8),(s[5] if len(s)>5 else TL),(s[6] if len(s)>6 else "middle")
            out.append(f'<text x="{_f(x)}" y="{_f(y)}" text-anchor="{anc}" font-family="monospace" font-size="{sz}" fill="{col}">{txt}</text>')
        elif t == 'co': # callout: x,y,n,lx,ly
            x,y,n = s[1],s[2],s[3]
            lx,ly = (s[4] if len(s)>4 else None),(s[5] if len(s)>5 else None)
            if lx is not None:
                out.append(f'<line x1="{_f(x)}" y1="{_f(y)}" x2="{_f(lx)}" y2="{_f(ly)}" stroke="{SW}" stroke-width="0.8" stroke-dasharray="3,2"/>')
            out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="7.5" fill="{SW}"/>')
            out.append(f'<text x="{_f(x)}" y="{_f(y+3.5)}" text-anchor="middle" font-family="monospace" font-size="8" fill="#fff" font-weight="bold">{n}</text>')
        elif t == 'gnd': # ground line: y,x1,x2
            gy,x1,x2 = s[1],s[2],s[3]
            out.append(f'<line x1="{_f(x1)}" y1="{_f(gy)}" x2="{_f(x2)}" y2="{_f(gy)}" stroke="{SP}" stroke-width="1.0"/>')
            for hx in range(int(x1)+4, int(x2), 10):
                out.append(f'<line x1="{hx}" y1="{_f(gy)}" x2="{hx-6}" y2="{_f(gy+8)}" stroke="{SP}" stroke-width="0.5"/>')
        elif t == 'cl': # centerline: x1,y1,x2,y2
            x1,y1,x2,y2 = s[1],s[2],s[3],s[4]
            out.append(f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" stroke="#1a3060" stroke-width="0.6" stroke-dasharray="6,3,2,3"/>')
        elif t == 'dim': # dimension: x1,y1,x2,y2,label,offset_dir(h|v)
            x1,y1,x2,y2,label,dr = s[1],s[2],s[3],s[4],s[5],s[6]
            if dr == 'h':
                my = min(y1,y2)-9
                out.append(f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x1)}" y2="{_f(my)}" stroke="{TD}" stroke-width="0.5"/>')
                out.append(f'<line x1="{_f(x2)}" y1="{_f(y2)}" x2="{_f(x2)}" y2="{_f(my)}" stroke="{TD}" stroke-width="0.5"/>')
                out.append(f'<line x1="{_f(x1)}" y1="{_f(my)}" x2="{_f(x2)}" y2="{_f(my)}" stroke="{TD}" stroke-width="0.8"/>')
                out.append(f'<text x="{_f((x1+x2)/2)}" y="{_f(my-3)}" text-anchor="middle" font-family="monospace" font-size="7" fill="{TD}">{label}</text>')
            else:
                mx = max(x1,x2)+9
                out.append(f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(mx)}" y2="{_f(y1)}" stroke="{TD}" stroke-width="0.5"/>')
                out.append(f'<line x1="{_f(x2)}" y1="{_f(y2)}" x2="{_f(mx)}" y2="{_f(y2)}" stroke="{TD}" stroke-width="0.5"/>')
                out.append(f'<line x1="{_f(mx)}" y1="{_f(y1)}" x2="{_f(mx)}" y2="{_f(y2)}" stroke="{TD}" stroke-width="0.8"/>')
                out.append(f'<text x="{_f(mx+4)}" y="{_f((y1+y2)/2+3)}" text-anchor="start" font-family="monospace" font-size="7" fill="{TD}">{label}</text>')
    out.append('</svg>')
    return ''.join(out)

def view_card(title, shapes, vw=260, vh=192):
    return (f'<div class="view-card">'
            f'<div class="view-label-bar">{title}</div>'
            f'{_shapes_svg(shapes, vw, vh)}'
            f'</div>')

# ─── Per-product data ─────────────────────────────────────────────────────────
# hotspot: (label, x, y, z,  nx, ny, nz)
# SVG shapes: use helper tuples above

PRODUCTS = [
  # ──────────────────────────────────────────────────────────────────────────
  { "id":"01","file":"01_spray_x.html","name":"Spray X",
    "orbit":"-30deg 68deg auto",
    "hotspots":[
      ("Chemical Tank",    0,-0.17, 0.22, 0, 0, 1),
      ("Spray Boom Array", 0,-0.32, 0,    0,-1, 0),
      ("Flow Control Valve",0,-0.33,0.14, 0, 0, 1),
      ("Folding Arm Latch",0.19,0.06,0,   1, 0, 0),
      ("Radar Altimeter",  0,-0.04, 0.15, 0, 0, 1),
    ],
    "front":[  # hexacopter front view
      ('cl',130,10,130,182),('cl',10,96,250,96),
      # center hub
      ('c',130,96,22,FB,SM),('c',130,96,14,FD,"#1a5aaa"),
      # 6 arms
      *[('l',130+66*__import__('math').cos(__import__('math').radians(d)),96+66*__import__('math').sin(__import__('math').radians(d)),
           130+16*__import__('math').cos(__import__('math').radians(d)),96+16*__import__('math').sin(__import__('math').radians(d)),
           SM,1.4) for d in [0,60,120,180,240,300]],
      # motor circles at arm ends
      *[('c',130+66*__import__('math').cos(__import__('math').radians(d)),96+66*__import__('math').sin(__import__('math').radians(d)),8,FD,"#00cc88") for d in [0,60,120,180,240,300]],
      # propellers at ends
      *[('l',130+66*__import__('math').cos(__import__('math').radians(d))-16,96+66*__import__('math').sin(__import__('math').radians(d)),
            130+66*__import__('math').cos(__import__('math').radians(d))+16,96+66*__import__('math').sin(__import__('math').radians(d)),
            "#00cc88",0.8) for d in [0,60,120,180,240,300]],
      # spray boom (below)
      ('r',30,148,200,6,FA,SA,1.2),
      # nozzles
      *[('l',x,154,x,162,SP,0.8) for x in range(40,222,26)],
      # tank below hub
      ('r',108,118,44,26,FB,SM),
      ('dim',30,154,230,154,"2180mm",'h'),
      ('co',220,30,1,130,96),('co',220,60,2,130,148),('co',220,90,3,130,133),
      ('co',220,120,4,143,96),('co',220,150,5,0,0),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('cl',130,10,130,182),('cl',10,96,250,96),
      ('c',130,96,22,FB,SM),('c',130,96,14,FD,"#1a5aaa"),
      ('l',130,118,130,148,SP,1.0),
      ('r',104,118,52,26,FB,SM),
      ('r',50,148,160,6,FA,SA,1.2),
      *[('l',x,154,x,162,SP,0.8) for x in range(60,205,28)],
      ('l',10,96,250,96,SP,0.6,"4,3"),
      ('dim',110,118,110,96,"690mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('cl',130,10,130,182),('cl',10,96,250,96),
      ('c',130,96,22,FB,SM),
      *[('l',130+66*__import__('math').cos(__import__('math').radians(d)),96+66*__import__('math').sin(__import__('math').radians(d)),
           130+16*__import__('math').cos(__import__('math').radians(d)),96+16*__import__('math').sin(__import__('math').radians(d)),
           SM,1.4) for d in [0,60,120,180,240,300]],
      *[('c',130+66*__import__('math').cos(__import__('math').radians(d)),96+66*__import__('math').sin(__import__('math').radians(d)),8,FD,"#00cc88") for d in [0,60,120,180,240,300]],
      ('r',108,112,44,18,FB,SM),
      ('dim',64,30,196,30,"2180mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"02","file":"02_scout.html","name":"Scout",
    "orbit":"-20deg 65deg auto",
    "hotspots":[
      ("Multispectral Array", 0,-0.060, 0.010, 0, 0, 1),
      ("Folding Pivot",       0.052,0.004,0.052, 1, 0, 0),
      ("Cooling Intake",      0, 0.028, 0.066, 0, 0, 1),
      ("Gimbal Module",       0,-0.040, 0,    0,-1, 0),
    ],
    "front":[
      ('cl',130,10,130,182),('cl',10,96,250,96),
      ('rr',98,82,64,28,4,FB,SM),('rr',106,76,48,10,2,FD,"#00cc88"),
      *[('l',130+78*__import__('math').cos(__import__('math').radians(d)),96+78*__import__('math').sin(__import__('math').radians(d)),
           130+35*__import__('math').cos(__import__('math').radians(d)),96+35*__import__('math').sin(__import__('math').radians(d)),
           SM,1.2) for d in [45,135,225,315]],
      *[('c',130+78*__import__('math').cos(__import__('math').radians(d)),96+78*__import__('math').sin(__import__('math').radians(d)),10,FD,"#00cc88") for d in [45,135,225,315]],
      ('c',130,116,10,FA,SA),('rr',114,124,32,16,3,FB,SM),
      ('dim',52,148,208,148,"340mm",'h'),
      ('co',220,32,1,130,116),('co',220,62,2,168,100),('co',220,92,3,130,76),('co',220,122,4,155,88),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('rr',90,82,80,28,4,FB,SM),('rr',98,76,64,10,2,FD,"#00cc88"),
      ('c',130,116,10,FA,SA),('rr',107,124,46,16,3,FB,SM),
      ('l',130,108,130,130,SP,1.0),
      ('dim',170,82,170,110,"110mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('rr',88,76,84,88,6,FB,SM),
      *[('l',130+78*__import__('math').cos(__import__('math').radians(d)),96+78*__import__('math').sin(__import__('math').radians(d)),
           130+42*__import__('math').cos(__import__('math').radians(d)),96+42*__import__('math').sin(__import__('math').radians(d)),
           SM,1.2) for d in [45,135,225,315]],
      *[('c',130+78*__import__('math').cos(__import__('math').radians(d)),96+78*__import__('math').sin(__import__('math').radians(d)),10,FD,"#00cc88") for d in [45,135,225,315]],
      ('dim',52,25,208,25,"340mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"03","file":"03_nest.html","name":"Nest",
    "orbit":"-20deg 60deg auto",
    "hotspots":[
      ("Drone Landing Pad",    0, 0.560, 0,    0, 1, 0),
      ("Retractable Roof",    -0.305,0.755, 0,  0, 1, 0),
      ("HVAC Unit",            0.66,0.02, 0,   1, 0, 0),
      ("Battery Magazine",    -0.40,-0.10, 0, -1, 0, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # main body box
      ('r',55,40,150,120,FB,SM),
      # roof left + right halves
      ('r',55,28,73,14,FP,"#00cc88",1.2),('r',132,28,73,14,FP,"#00cc88",1.2),
      # landing pad
      ('r',75,14,110,16,FD,SA,1.2),('c',130,22,10,'none',"#ff8c00",1.0),
      # battery magazine left
      ('r',55,50,30,80,FD,SP,1.0),
      # HVAC right
      ('r',175,60,10,50,FD,SP),
      # ground
      ('gnd',160,50,210),
      ('dim',55,165,205,165,"1200mm",'h'),('dim',215,40,215,160,"1400mm",'v'),
      ('co',28,25,1,130,22),('co',28,55,2,92,28),('co',28,85,3,179,85),('co',28,115,4,70,90),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('r',72,40,116,120,FB,SM),
      ('r',72,28,56,14,FP,"#00cc88",1.2),('r',132,28,56,14,FP,"#00cc88",1.2),
      ('r',88,14,84,16,FD,SA,1.2),
      ('r',175,60,8,50,FD,SP),
      ('gnd',160,62,198),
      ('dim',215,40,215,160,"1400mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',55,40,150,112,FB,SM),
      ('r',75,52,110,80,FD,"#00cc88",1.2),
      ('c',130,92,18,'none',"#ff8c00",1.0),
      ('l',112,92,148,92,"#ff8c00",0.8),('l',130,74,130,110,"#ff8c00",0.8),
      ('dim',55,20,205,20,"1200mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"04","file":"04_watchtower.html","name":"Watchtower",
    "orbit":"-15deg 78deg auto",
    "hotspots":[
      ("PTZ Dome",          0, 5.30, 0,   0, 1, 0),
      ("Solar Panel Mount", 0, 4.68, 0.54, 0, 0, 1),
      ("LTE Antenna",       0.06,5.55, 0,  0, 1, 0),
      ("AI Enclosure",      0.12,3.20, 0,  1, 0, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # mast (tall pole)
      ('r',124,15,12,145,FB,SM),
      # concrete base
      ('r',100,158,60,16,FD,SP),
      # solar panel extending right
      ('r',136,30,60,28,FA,SA,1.2),('r',138,32,56,24,"rgba(0,100,200,0.35)",SA),
      # AI enclosure on mast
      ('r',136,78,26,16,FD,SP),
      # PTZ dome on top
      ('e',130,18,16,10,FP,"#00cc88",),
      # antennas
      ('l',126,12,126,5,SP,0.8),('l',134,13,134,7,SP,0.8),
      ('gnd',174,90,170),
      ('dim',60,15,196,15,"6000mm",'v'),  # vertical height
      ('co',220,28,1,130,18),('co',220,56,2,166,44),('co',220,84,3,126,8),('co',220,112,4,149,86),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('r',124,15,12,145,FB,SM),
      ('r',100,158,60,16,FD,SP),
      ('r',136,76,20,14,FD,SP),
      ('e',130,18,16,10,FP,"#00cc88"),
      ('gnd',174,94,166),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      # cross section of mast
      ('c',130,96,10,FB,SM),
      # solar panel above/beside
      ('r',140,60,60,28,FA,SA),
      # base flange
      ('r',112,110,36,36,'none',SP,0.8),
      ('dim',112,20,188,20,"780mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"05","file":"05_soilnode.html","name":"Soilnode",
    "orbit":"-10deg 72deg auto",
    "hotspots":[
      ("Solar Dome Cap",    0, 0.152, 0,   0, 1, 0),
      ("NPK Probes",        0,-0.200, 0.016,0, 0, 1),
      ("Threaded Seal",     0,-0.005, 0,   0, 0, 1),
    ],
    "front":[
      ('cl',130,10,130,182),
      # above-ground body
      ('c',130,70,22,FB,SM),('c',130,70,14,FD,SP),
      # solar dome
      ('e',130,50,16,10,FA,SA),
      # probe shaft
      ('r',125,92,10,40,FB,SM),
      # probe taper
      ('p',[(125,132),(135,132),(130,148)],FB,SM),
      # NPK probes (3 thin rods at bottom)
      *[('l',x,138,x,155,SA,0.8) for x in [122,130,138]],
      # ground line
      ('gnd',92,80,180),
      # seal collar
      ('r',122,88,16,8,FP,"#00cc88"),
      ('dim',155,50,155,148,"310mm",'v'),
      ('co',30,30,1,130,50),('co',30,60,2,130,88),('co',30,90,3,130,148),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('c',130,70,22,FB,SM),
      ('e',130,50,16,10,FA,SA),
      ('r',125,92,10,40,FB,SM),
      ('p',[(125,132),(135,132),(130,148)],FB,SM),
      ('gnd',92,80,180),
      ('r',122,88,16,8,FP,"#00cc88"),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('c',130,96,22,FB,SM),
      ('c',130,96,14,FA,SA),
      # NPK probes
      ('c',130,82,3,FA,SA),('c',119,103,3,FA,SA),('c',141,103,3,FA,SA),
      ('dim',108,20,152,20,"92mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"06","file":"06_feedpro.html","name":"Feedpro",
    "orbit":"-25deg 68deg auto",
    "hotspots":[
      ("Hopper Lid",       0, 0.90, 0,    0, 1, 0),
      ("Auger Output Spout",0.44,0.00,0,  1, 0, 0),
      ("Control Box",      0.32,0.32,0.32,0, 0, 1),
      ("Load Cell Mount",  0.40,-0.74,-0.28, 0,-1, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # main frame
      ('r',72,35,116,120,FB,SM),
      # hopper (tapered)
      ('p',[(90,35),(170,35),(160,65),(100,65)],FP,SM),
      # lid
      ('r',88,26,104,10,FP,"#00cc88"),
      # auger housing
      ('r',72,95,116,20,FP,SM),
      # auger output right
      ('r',185,100,16,10,FA,SA),
      # control box
      ('r',162,50,20,28,FD,SP),('r',164,52,16,14,FD,"#00aaff",0.8),
      # legs
      *[('r',x,155,6,16,FD,SP) for x in [80,100,168,188]],
      ('gnd',171,75,210),
      ('dim',215,35,215,155,"1480mm",'v'),('dim',72,176,188,176,"850mm",'h'),
      ('co',28,28,1,130,26),('co',28,56,2,196,105),('co',28,84,3,172,64),('co',28,112,4,84,163),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('r',88,35,84,120,FB,SM),
      ('p',[(102,35),(158,35),(152,65),(108,65)],FP,SM),
      ('r',86,26,88,10,FP,"#00cc88"),
      ('r',88,95,84,20,FP,SM),
      *[('r',x,155,6,16,FD,SP) for x in [94,158]],
      ('gnd',171,82,186),
      ('dim',182,35,182,155,"1480mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',72,42,116,112,FB,SM),
      ('r',90,42,100,50,FP,SM),
      ('r',188,88,16,10,FA,SA),
      ('dim',72,20,188,20,"850mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"07","file":"07_herdtag.html","name":"Herdtag",
    "orbit":"15deg 60deg auto",
    "hotspots":[
      ("TPU Sheath",    0, 0, 0,      0, 0, 1),
      ("Piercing Pin",  0,-0.012, 0,  0,-1, 0),
      ("PCB Assembly",  0, 0.002, 0,  0, 1, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # main body (rounded rect)
      ('rr',82,78,96,36,6,FP,SM),
      # electronics
      ('r',94,84,72,18,FD,SP),
      # pin top
      ('r',127,72,6,8,FP,"#00cc88"),
      # pin bottom (piercing)
      ('r',127,114,6,12,FP,SM),
      # LED
      ('c',150,84,3,FA,SA),
      ('dim',82,128,178,128,"48mm",'h'),('dim',196,78,196,114,"36mm",'v'),
      ('co',30,35,1,130,96),('co',30,65,2,130,120),('co',30,95,3,130,93),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      # edge-on - very thin
      ('r',124,78,12,36,FP,SM),
      ('r',127,72,6,8,FP,"#00cc88"),
      ('r',127,114,6,12,FP,SM),
      ('dim',145,78,145,114,"15mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('rr',82,78,96,36,6,FP,SM),
      ('r',94,84,72,24,FD,SP),
      ('c',150,92,3,FA,SA),
      ('dim',82,60,178,60,"48mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"08","file":"08_aquasense.html","name":"Aquasense",
    "orbit":"-15deg 65deg auto",
    "hotspots":[
      ("Solar Panel Array",  0, 0.128, 0,  0, 1, 0),
      ("Grab Handles",       0.235,0.040,0,1, 0, 0),
      ("Probe Cage",         0,-0.170, 0,  0,-1, 0),
      ("Ballast Module",     0,-0.370, 0,  0,-1, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # torus cross section (two lobes)
      ('e',90,90,24,22,FB,SM),('e',170,90,24,22,FB,SM),
      # solar cap top
      ('r',96,58,68,16,FA,SA,1.2),('r',100,56,60,12,"rgba(0,80,180,0.4)",SA),
      # central hub
      ('r',116,74,28,18,FD,SP),
      # probe cage below
      ('r',124,112,12,36,FP,SM),('r',118,124,24,6,FP,SM),('r',118,136,24,6,FP,SM),
      # ballast
      ('c',130,162,10,FD,"#8888aa"),
      # grab handles
      ('r',71,82,10,12,'none',SP,0.8),('r',179,82,10,12,'none',SP,0.8),
      ('dim',66,176,194,176,"520mm",'h'),('dim',210,56,210,168,"760mm",'v'),
      ('co',28,28,1,130,62),('co',28,58,2,184,88),('co',28,88,3,130,130),('co',28,118,4,130,162),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('e',130,90,24,22,FB,SM),
      ('r',110,58,40,16,FA,SA),
      ('r',116,74,28,18,FD,SP),
      ('r',124,112,12,36,FP,SM),
      ('c',130,162,10,FD,"#8888aa"),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      # top-down: torus ring
      ('e',130,96,64,64,'none',SM,1.4),('e',130,96,26,26,FB,SM),
      ('r',96,72,68,16,FA,SA),
      ('dim',66,28,194,28,"520mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"09","file":"09_fencegrid.html","name":"Fencegrid",
    "orbit":"-25deg 62deg auto",
    "hotspots":[
      ("Status LED",   0.072,0.022, 0.058, 0, 0, 1),
      ("U-Bolt Mount", 0,-0.062, 0,       0,-1, 0),
      ("Antenna Radome",0,0.034, 0,       0, 1, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      ('rr',72,72,116,52,3,FB,SM),
      # ribs
      *[('l',x,72,x,124,SP,0.6) for x in [112,142,172]],
      # antenna dome on top
      ('e',130,68,18,6,FP,"#00cc88"),
      # solar strip on top face
      ('r',86,68,88,4,FA,SA),
      # status LED
      ('c',176,78,4,FA,SA),
      # IR sensors on ends
      ('r',72,82,8,10,FD,SP),('r',180,82,8,10,FD,SP),
      # U-bolt mount below
      ('r',118,124,24,4,FD,SP),
      *[('l',122,128,122,138,SP,0.8),('l',138,128,138,138,SP,0.8),('l',122,138,138,138,SP,0.8)],
      ('dim',72,150,188,150,"180mm",'h'),('dim',205,72,205,124,"58mm",'v'),
      ('co',28,34,1,176,78),('co',28,64,2,130,130),('co',28,94,3,130,66),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('rr',82,72,76,52,3,FB,SM),
      ('e',130,68,12,5,FP,"#00cc88"),
      ('r',88,68,64,4,FA,SA),
      ('r',118,124,24,4,FD,SP),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('rr',72,72,116,76,3,FB,SM),
      *[('l',x,72,x,148,SP,0.6) for x in [112,142,172]],
      ('r',86,68,88,6,FA,SA),
      ('dim',72,55,188,55,"180mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"10","file":"10_hub.html","name":"Hub",
    "orbit":"-20deg 62deg auto",
    "hotspots":[
      ("Antenna Array",  0, 0.020,  0.085, 0, 0, 1),
      ("Cooling Vents",  0.215,0,    0,    1, 0, 0),
      ("Industrial I/O",-0.215,0,    0,   -1, 0, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # main box (flat)
      ('r',58,72,144,56,FB,SM),
      # antenna array on top
      *[('l',x,68,x,58,SP,0.8) for x in range(74,188,14)],
      *[('c',x,58,4,FP,"#00cc88") for x in range(74,188,14)],
      # IO ports on left
      *[('r',52,y,8,6,FD,SP) for y in range(80,120,10)],
      # cooling fins on right
      *[('r',200,y,8,4,FD,SP) for y in range(80,120,10)],
      # status LEDs on front face
      *[('c',80+x*12,80,3,FA,SA) for x in range(5)],
      ('dim',58,145,202,145,"420mm",'h'),('dim',215,72,215,128,"160mm",'v'),
      ('co',28,28,1,130,58),('co',28,58,2,203,100),('co',28,88,3,47,100),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('r',82,72,96,56,FB,SM),
      *[('r',94+x*8,68,4,5,FD,"#00cc88") for x in range(5)],
      *[('r',78,y,6,4,FD,SP) for y in range(80,120,10)],
      ('dim',190,72,190,128,"160mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',58,68,144,64,FB,SM),
      *[('l',x,68,x,62,SP,0.8) for x in range(72,202,16)],
      ('dim',58,42,202,42,"420mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"11","file":"11_crewlink.html","name":"CrewLink",
    "orbit":"15deg 65deg auto",
    "hotspots":[
      ("E-Ink Display",  0, 0.006, 0.009,  0, 0, 1),
      ("SOS Button",     0.020,0.006,0.009,0, 0, 1),
      ("LoRa Antenna",   0,-0.015, 0.0085, 0, 0, 1),
    ],
    "front":[
      ('cl',130,10,130,182),
      ('rr',96,72,68,44,4,FP,SM),
      # display
      ('r',102,76,40,28,FD,"#00aaff",1.0),
      # SOS button
      ('c',155,82,5,FA,"#ff4444",1.5),
      # port at bottom
      ('r',126,116,8,4,FD,SP),
      # antenna stub
      ('r',127,68,6,5,FD,SP),
      ('dim',96,130,164,130,"65mm",'h'),('dim',180,72,180,116,"45mm",'v'),
      ('co',28,38,1,122,90),('co',28,68,2,155,82),('co',28,98,3,130,68),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('rr',116,72,28,44,4,FP,SM),
      ('r',118,76,18,28,FD,"#00aaff",1.0),
      ('r',128,68,4,5,FD,SP),
      ('dim',155,72,155,116,"18mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('rr',96,80,68,32,4,FP,SM),
      ('r',102,84,40,20,FD,"#00aaff"),
      ('dim',96,60,164,60,"65mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"12","file":"12_agrimule.html","name":"AgriMule",
    "orbit":"-25deg 68deg auto",
    "hotspots":[
      ("LiDAR Puck",        0, 0.580, 0,    0, 1, 0),
      ("Track Assembly",    0.72,-0.04, 0.60,1, 0, 0),
      ("Tow Hitch",        -1.20, 0,   0,  -1, 0, 0),
      ("Track Tensioner",   1.72,-0.04, 0.60,1, 0, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # left track
      ('rr',30,78,38,80,8,FD,SM),
      # right track
      ('rr',192,78,38,80,8,FD,SM),
      # body
      ('r',68,55,124,80,FB,SM),
      # LiDAR dome on top
      ('c',130,48,14,FA,SA),
      # solar panels
      ('r',80,44,100,14,FA,SA),
      # camera/sensors front
      ('r',118,62,24,16,FD,SP),
      ('dim',30,172,230,172,"2400mm",'h'),('dim',244,55,244,135,"850mm",'v'),
      ('co',28,28,1,130,48),('co',28,58,2,213,118),('co',28,88,3,0,0),('co',28,118,4,0,0),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('rr',40,78,180,80,8,FD,SM),
      ('r',70,55,120,80,FB,SM),
      ('c',130,48,14,FA,SA),
      # tow hitch at back
      ('r',220,90,12,20,FP,SM),
      ('gnd',158,22,238),
      ('dim',210,55,210,135,"850mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      # two tracks
      ('rr',30,62,38,68,8,FD,SM),('rr',192,62,38,68,8,FD,SM),
      ('r',68,68,124,52,FB,SM),
      ('c',130,94,14,FA,SA),
      ('dim',30,28,230,28,"2400mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"13","file":"13_rowplanter.html","name":"RowPlanter",
    "orbit":"0deg 62deg auto",
    "hotspots":[
      ("Electric Seed Meter",  0, 0.62, 0,    0, 0, 1),
      ("Closing Wheel Assembly",0,-0.02,-0.36, 0,-1, 0),
      ("Air Hose Routing",     0, 0.62, 0,    0, 0,-1),
    ],
    "front":[  # very wide implement
      ('cl',130,10,130,182),
      # main toolbar beam
      ('r',10,68,240,18,FB,SM),
      # 8 row units hanging below
      *[('r',18+x*30,86,12,60,FP,SM) for x in range(8)],
      # seed meter boxes
      *[('r',16+x*30,86,16,14,FD,SP) for x in range(8)],
      # closing wheels (small circles at bottom of each row unit)
      *[('c',24+x*30,150,6,'none',SA,1.0) for x in range(8)],
      ('dim',10,170,250,170,"6000mm",'h'),('dim',254,68,254,150,"1400mm",'v'),
      ('co',18,28,1,34,90),('co',18,58,2,24,150),('co',18,88,3,130,68),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('r',90,68,80,18,FB,SM),
      ('r',118,86,24,60,FP,SM),('r',114,86,32,14,FD,SP),
      ('c',130,150,6,'none',SA,1.0),
      ('dim',186,68,186,150,"1400mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',10,68,240,50,FB,SM),
      *[('l',18+x*30,68,18+x*30,118,SP,0.8) for x in range(8)],
      ('dim',10,42,250,42,"6000mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"14","file":"14_terraplanter.html","name":"TerraPlanter",
    "orbit":"-25deg 68deg auto",
    "hotspots":[
      ("Hydraulic Auger Head",  1.60, 0.12, 0,  1, 0, 0),
      ("Sapling Gripper",       1.50, 0.70, 0,  0, 1, 0),
      ("Rotary Magazine",       0,    0.695,0,   0, 1, 0),
      ("Canopy Frame",          0,    0.695, 0.42,0, 0, 1),
    ],
    "front":[
      ('cl',130,10,130,182),
      # 4-wheel chassis
      *[('c',x,y,16,FD,SM) for x,y in [(60,140),(200,140),(60,100),(200,100)]],
      # main body frame
      ('r',70,52,120,100,FB,SM),
      # arm extending up-right
      ('r',184,36,12,80,FP,"#00cc88",1.2),
      # auger head at top of arm
      ('e',196,32,18,12,FD,SA),
      # rotary magazine
      ('c',130,80,20,FA,SA),
      # canopy
      ('r',72,44,116,10,'none',"#00cc88",0.8),
      ('dim',44,170,216,170,"3500mm",'h'),('dim',226,36,226,155,"2200mm",'v'),
      ('co',28,28,1,190,32),('co',28,58,2,192,44),('co',28,88,3,130,80),('co',28,118,4,130,44),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      *[('c',x,y,16,FD,SM) for x,y in [(68,140),(192,140)]],
      ('r',78,52,104,100,FB,SM),
      ('r',170,36,12,80,FP,"#00cc88",1.2),
      ('e',182,32,18,12,FD,SA),
      ('c',130,80,20,FA,SA),
      ('dim',214,52,214,152,"2200mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',68,72,124,56,FB,SM),
      *[('c',x,y,16,FD,SM) for x,y in [(68,72),(192,72),(68,128),(192,128)]],
      ('c',130,100,20,FA,SA),
      ('r',184,68,12,64,FP,"#00cc88"),
      ('dim',52,42,208,42,"3500mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"15","file":"15_microweeder.html","name":"MicroWeeder",
    "orbit":"-20deg 68deg auto",
    "hotspots":[
      ("50W Fiber Laser",      0, 0.09, 0,    0,-1, 0),
      ("High-Speed Camera",    0, 0.32, 0,    0, 0, 1),
      ("Delta Arm Pivot",      0, 0.35, 0.48, 0, 0, 1),
    ],
    "front":[
      ('cl',130,10,130,182),
      # outer frame rails
      ('r',38,38,184,130,FB,SM),('r',52,52,156,100,'none',SP,0.6),
      # delta arms (3 arms from top platform to laser head)
      ('l',130,56,94,120,SM,1.2),('l',130,56,166,120,SM,1.2),
      ('l',130,56,130,120,SM,1.4),
      # laser head
      ('c',130,124,12,FA,"#ff4444",1.5),
      # camera pod
      ('r',116,48,28,12,FD,SP),
      # side actuators
      *[('r',x,60,8,60,FP,SM) for x in [38,214]],
      ('dim',38,174,222,174,"1600mm",'h'),('dim',234,38,234,168,"800mm",'v'),
      ('co',28,28,1,130,124),('co',28,58,2,130,54),('co',28,88,3,94,120),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('r',56,38,148,130,FB,SM),
      ('l',130,56,100,120,SM,1.2),('l',130,56,160,120,SM,1.2),
      ('c',130,124,12,FA,"#ff4444",1.5),
      ('r',106,48,48,12,FD,SP),
      ('dim',216,38,216,168,"1200mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',38,38,184,116,FB,SM),
      # delta arm triangle from above
      ('p',[(94,100),(166,100),(130,68)],FP,SA),
      ('c',130,84,12,FA,"#ff4444"),
      ('dim',38,20,222,20,"1600mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"16","file":"16_brushcrusher.html","name":"BrushCrusher",
    "orbit":"-20deg 68deg auto",
    "hotspots":[
      ("Tungsten Carbide Teeth",1.60, 0.12, 0,  1, 0, 0),
      ("Hydraulic Motor Cover", 1.72,-0.04, 0.60,1, 0, 0),
      ("Steel Deflector Shield",0,    0.44, 0,   0, 1, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # main frame
      ('r',20,40,220,110,FB,SM),
      # front mulcher drum
      ('rr',20,88,50,40,6,FD,SM),
      # drum teeth
      *[('r',22+x*6,88,3,40,"rgba(255,200,0,0.5)","#ffcc00",0.8) for x in range(8)],
      # hydraulic motor
      ('c',46,108,12,FD,"#00cc88"),
      # deflector shield on top
      ('r',20,38,220,6,FP,"#00cc88",1.2),
      # 3-pt hitch rear
      *[('r',x,110,8,30,FP,SM) for x in [228,236]],
      ('dim',20,165,240,165,"3800mm",'h'),('dim',250,40,250,150,"1800mm",'v'),
      ('co',28,28,1,46,98),('co',28,58,2,60,108),('co',28,88,3,130,38),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      ('r',55,40,150,110,FB,SM),
      ('rr',55,88,40,40,6,FD,SM),
      *[('r',57+x*5,88,3,40,"rgba(255,200,0,0.5)","#ffcc00",0.8) for x in range(7)],
      ('c',75,108,12,FD,"#00cc88"),
      ('r',55,38,150,6,FP,"#00cc88",1.2),
      ('dim',218,40,218,150,"1800mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',20,62,220,68,FB,SM),
      ('rr',20,98,50,28,6,FD,SM),
      ('dim',20,30,240,30,"3800mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },

  # ──────────────────────────────────────────────────────────────────────────
  { "id":"17","file":"17_omniharvester.html","name":"OmniHarvester",
    "orbit":"-25deg 65deg auto",
    "hotspots":[
      ("Soft-Grip End Effector",0, 2.82, 0.60, 0, 0, 1),
      ("Stereo Vision Camera",  0, 2.46,-1.20, 0, 0,-1),
      ("Central Conveyor",      0, 0.30, 0,    0,-1, 0),
      ("Drive Wheel",           1.20,-0.38, 1.20,1, 0, 0),
    ],
    "front":[
      ('cl',130,10,130,182),
      # 4 wheels
      *[('c',x,y,20,FD,SM) for x,y in [(64,150),(196,150),(64,100),(196,100)]],
      # main body
      ('r',72,30,116,128,FB,SM),
      # arm array (6 arms, 3 per side shown as boxes)
      *[('r',184,34+y*24,14,16,FP,"#00cc88") for y in range(3)],
      *[('r',62,34+y*24,14,16,FP,"#00cc88") for y in range(3)],
      # end effectors
      *[('e',196,42+y*24,8,4,FA,SA) for y in range(3)],
      # conveyor belt (bottom)
      ('r',80,142,100,12,FD,SM),
      # stereo cameras (front array)
      *[('r',96+x*22,26,14,10,FD,SP) for x in range(3)],
      ('dim',44,178,216,178,"4500mm",'h'),('dim',230,30,230,158,"3000mm",'v'),
      ('co',28,28,1,192,42),('co',28,58,2,110,26),('co',28,88,3,130,148),('co',28,118,4,196,150),
      ('tx',130,185,"FRONT VIEW",7,TD),
    ],
    "side":[
      *[('c',x,y,20,FD,SM) for x,y in [(68,150),(192,150)]],
      ('r',76,30,108,128,FB,SM),
      *[('r',182,34+y*24,14,16,FP,"#00cc88") for y in range(3)],
      *[('e',194,42+y*24,8,4,FA,SA) for y in range(3)],
      ('r',88,142,84,12,FD,SM),
      ('dim',220,30,220,158,"3000mm",'v'),
      ('tx',130,185,"SIDE VIEW",7,TD),
    ],
    "top":[
      ('r',64,50,132,82,FB,SM),
      *[('c',x,y,20,FD,SM) for x,y in [(64,50),(196,50),(64,132),(196,132)]],
      ('r',88,60,84,62,FD,SM),
      *[('r',184,52+y*22,24,14,FP,"#00cc88") for y in range(3)],
      ('dim',44,24,216,24,"4500mm",'h'),
      ('tx',130,185,"TOP VIEW",7,TD),
    ],
  },
]

# ─── Hotspot CSS + 2D view CSS (injected into each page) ─────────────────────
EXTRA_CSS = """
  <style>
    /* ── Hotspot annotations ─────────────────────────────── */
    button[slot^="hotspot-"] {
      background: rgba(0,120,255,0.85);
      border: 2px solid #44aaff;
      border-radius: 50%;
      width: 20px; height: 20px;
      cursor: pointer; padding: 0;
      position: relative;
      transition: background 0.15s, transform 0.15s;
      box-shadow: 0 0 8px rgba(0,120,255,0.5);
    }
    button[slot^="hotspot-"]:hover { transform: scale(1.25); background: rgba(0,160,255,0.95); }
    button[slot^="hotspot-"]:not([data-visible]) {
      background: transparent; border-color: transparent; pointer-events: none;
    }
    button[slot^="hotspot-"]:not([data-visible]) .hs-label { display: none; }
    .hs-dot {
      width: 6px; height: 6px; background: #fff; border-radius: 50%;
      position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
    }
    .hs-label {
      background: rgba(4,12,34,0.96);
      border: 1px solid rgba(0,120,255,0.5);
      border-left: 3px solid #0088ff;
      border-radius: 0 5px 5px 0;
      color: #a8d0ff;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px; font-weight: 500;
      padding: 4px 12px 4px 8px;
      position: absolute; left: 26px; top: 50%;
      transform: translateY(-50%);
      white-space: nowrap; pointer-events: none;
      letter-spacing: 0.04em;
    }
    /* ── 2D Technical Views ──────────────────────────────── */
    .views-section { margin: 28px 0 0; }
    .views-section h2 { margin-bottom: 14px; }
    .views-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }
    .view-card {
      background: #060c1b;
      border: 1px solid #1b2f5e;
      border-radius: 6px;
      overflow: hidden;
    }
    .view-card svg { display: block; width: 100%; height: auto; }
    .view-label-bar {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9px; letter-spacing: 0.14em;
      color: #3355aa; text-align: center;
      padding: 5px 0 4px;
      background: #030710;
      border-bottom: 1px solid #0e1e44;
      text-transform: uppercase;
    }
  </style>
"""

# ─── Hotspot HTML builder ─────────────────────────────────────────────────────
def build_hotspots(hotspots):
    lines = []
    for i,(label,x,y,z,nx,ny,nz) in enumerate(hotspots):
        lines.append(
            f'      <button slot="hotspot-{i}" '
            f'data-position="{x:.3f} {y:.3f} {z:.3f}" '
            f'data-normal="{nx:.1f} {ny:.1f} {nz:.1f}" '
            f'data-visibility-attribute="visible">'
            f'<div class="hs-dot"></div>'
            f'<div class="hs-label">{label}</div></button>'
        )
    return '\n'.join(lines)

# ─── 2D views section HTML builder ───────────────────────────────────────────
def build_views_section(prod):
    front = view_card("Front View", prod["front"])
    side  = view_card("Side View",  prod["side"])
    top   = view_card("Top View",   prod["top"])
    return (
        f'\n  <section class="views-section">\n'
        f'    <h2>2D Technical Views</h2>\n'
        f'    <div class="views-grid">\n'
        f'      {front}\n      {side}\n      {top}\n'
        f'    </div>\n'
        f'  </section>\n'
    )

# ─── Model-viewer attribute updater ──────────────────────────────────────────
NEW_MV_ATTRS = [
    ('environment-image', 'neutral'),
    ('shadow-intensity',  '2.5'),
    ('shadow-softness',   '0.35'),
    ('exposure',          '1.2'),
    ('min-camera-orbit',  'auto auto 0.4m'),
    ('max-camera-orbit',  'auto auto 10m'),
]

def update_mv_tag(tag_str, orbit):
    # Set camera-orbit
    tag_str = re.sub(r'camera-orbit="[^"]*"', f'camera-orbit="{orbit}"', tag_str)
    if 'camera-orbit=' not in tag_str:
        tag_str = tag_str.replace('<model-viewer ', f'<model-viewer camera-orbit="{orbit}" ')
    # Add/overwrite other attrs
    for attr, val in NEW_MV_ATTRS:
        tag_str = re.sub(rf'{attr}="[^"]*"', '', tag_str)
        tag_str = tag_str.replace('<model-viewer ', f'<model-viewer {attr}="{val}" ')
    return tag_str

# ─── Main update function ─────────────────────────────────────────────────────
def update_file(prod):
    path = os.path.join(BASE, prod["file"])
    with open(path, encoding='utf-8') as f:
        html = f.read()

    # 1. Inject CSS before </head>
    if 'hs-label' not in html:
        html = html.replace('</head>', EXTRA_CSS + '</head>', 1)

    # 2. Update model-viewer opening tag (preserve the base64 blob inside it)
    def patch_mv(m):
        tag = m.group(0)
        tag = update_mv_tag(tag, prod["orbit"])
        return tag
    html = re.sub(r'<model-viewer [^>]*>', patch_mv, html, count=1)

    # 3. Inject hotspot buttons just before </model-viewer>
    hs_html = build_hotspots(prod["hotspots"])
    if 'slot="hotspot-0"' not in html:
        html = html.replace('</model-viewer>', hs_html + '\n    </model-viewer>', 1)

    # 4. Inject 2D views section after the closing </section> of the 3D viewer
    views_html = build_views_section(prod)
    if '<section class="views-section">' not in html:
        # Find the closing tag of the 360° section
        html = re.sub(
            r'(</section>)(\s*\n\s*<div class="grid)',
            lambda m: m.group(1) + views_html + m.group(2),
            html, count=1
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓  {prod['file']}")

# ─── Run ──────────────────────────────────────────────────────────────────────
print("Famtech AgriCore — HTML upgrade")
for prod in PRODUCTS:
    update_file(prod)
print(f"\nDone. {len(PRODUCTS)} files updated.")
