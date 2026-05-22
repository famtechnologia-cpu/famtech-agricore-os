#!/usr/bin/env python3
"""
Replace the 2D technical view section in all 17 HTML files with
realistic isometric product illustrations rendered in SVG.
"""
import re, os, math

BASE = "/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts"

# ── ISO renderer ──────────────────────────────────────────────────────────────
# Material palette: [top_face, front_face, side_face]
M = {
  'ALU':    ['#cdd2da','#9aa0ae','#626876'],
  'STEEL':  ['#b0b6c2','#808694','#505660'],
  'CARBON': ['#363840','#22242a','#10121a'],
  'HDPE':   ['#f2eedf','#c4c0ae','#8c8a80'],
  'PC':     ['#c4e4f6','#88c0e2','#4882b8'],  # polycarbonate
  'SOLAR':  ['#1e3468','#101e40','#080e22'],
  'SOLAR2': ['#243e7c','#14244e','#0a1232'],
  'RUBBER': ['#2e2e2e','#1c1c1c','#0c0c0c'],
  'TPU':    ['#b07820','#806010','#503a08'],
  'ORANGE': ['#f09030','#c06018','#884010'],
  'GREEN':  ['#38cc7c','#18a050','#0a6830'],
  'DARK':   ['#2c303c','#1c2030','#0c1020'],
  'YELLOW': ['#ecd820','#b8b010','#7a7408'],
  'SCREEN': ['#2060b0','#103880','#081840'],
  'LED_G':  ['#50ff88','#20cc54','#0c7a30'],
  'LED_B':  ['#4080ff','#2050c0','#102070'],
  'WATER':  ['#60b4f0','#3080c0','#184880'],
  'CONC':   ['#8a8678','#6a6658','#4a4840'],
  'LEAD':   ['#5c6070','#3c4050','#1c2030'],
  'RED':    ['#e03030','#a01818','#680808'],
}

def _f(v): return f"{v:.1f}"

class ISO:
    """Isometric SVG renderer. World: Y-up, right-hand. View: front-right-top."""
    def __init__(self, scale=50, cx=260, cy=260):
        self.s  = scale
        self.cx = cx
        self.cy = cy
        self._parts = []   # (sort_depth, svg_str)
        self._defs  = {}   # gradient id → svg def

    def _proj(self, x, y, z):
        sx = self.cx + (x - z) * self.s * 0.866
        sy = self.cy - y * self.s + (x + z) * self.s * 0.5
        return sx, sy

    def _pts(self, pts):
        return " ".join(f"{_f(x)},{_f(y)}" for x,y in pts)

    def _poly(self, pts, fill, stroke="#00000033", sw=0.6):
        return f'<polygon points="{self._pts(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

    def box(self, x, y, z, W, H, D, mat='STEEL', opacity=1.0):
        """Isometric box. (x,y,z) = bottom-front-left corner."""
        P = self._proj
        # 8 corners
        c = {
          'bfl': P(x,  y,  z),   'bfr': P(x+W,y,  z),
          'bbl': P(x,  y,  z+D), 'bbr': P(x+W,y,  z+D),
          'tfl': P(x,  y+H,z),   'tfr': P(x+W,y+H,z),
          'tbl': P(x,  y+H,z+D),'tbr': P(x+W,y+H,z+D),
        }
        top   = [c['tfl'],c['tfr'],c['tbr'],c['tbl']]
        front = [c['bfl'],c['bfr'],c['tfr'],c['tfl']]
        side  = [c['bfr'],c['bbr'],c['tbr'],c['tfr']]
        cols = M.get(mat, M['STEEL'])
        oa = f' opacity="{opacity}"' if opacity < 1 else ''
        depth = x - z
        for face_pts, col in [(top, cols[0]), (front, cols[1]), (side, cols[2])]:
            self._parts.append((depth, f'<polygon points="{self._pts(face_pts)}" fill="{col}" stroke="rgba(0,0,0,0.25)" stroke-width="0.5"{oa}/>'))

    def cyl_v(self, cx, cy, cz, r, h, mat='STEEL', seg=14):
        """Vertical cylinder in isometric view (approximated)."""
        P = self._proj
        # Top ellipse center
        tc = P(cx, cy+h, cz)
        bc = P(cx, cy, cz)
        # Approximate: render as a front-facing box + top ellipse
        # Use a parallelogram for the body (front quad)
        top_l = P(cx-r, cy+h, cz)
        top_r = P(cx+r, cy+h, cz)
        bot_l = P(cx-r, cy, cz)
        bot_r = P(cx+r, cy, cz)
        # Side face (right)
        s_tl = P(cx+r, cy+h, cz)
        s_tr = P(cx+r, cy+h, cz+r*0.5)
        s_br = P(cx+r, cy, cz+r*0.5)
        s_bl = P(cx+r, cy, cz)
        cols = M.get(mat, M['STEEL'])
        depth = cx - cz
        # Body front
        self._parts.append((depth, f'<polygon points="{self._pts([bot_l,bot_r,top_r,top_l])}" fill="{cols[1]}" stroke="rgba(0,0,0,0.2)" stroke-width="0.5"/>'))
        # Body side
        self._parts.append((depth+0.01, f'<polygon points="{self._pts([s_bl,s_br,s_tr,s_tl])}" fill="{cols[2]}" stroke="rgba(0,0,0,0.2)" stroke-width="0.5"/>'))
        # Top ellipse (squished)
        rx = r * self.s * 1.0
        ry = r * self.s * 0.3
        self._parts.append((depth+0.02, f'<ellipse cx="{_f(tc[0])}" cy="{_f(tc[1])}" rx="{_f(rx)}" ry="{_f(ry)}" fill="{cols[0]}" stroke="rgba(0,0,0,0.2)" stroke-width="0.5"/>'))

    def cyl_h(self, cx, cy, cz, r, h, axis='x', mat='STEEL'):
        """Horizontal cylinder (X or Z axis)."""
        if axis == 'x':
            self.box(cx-h/2, cy-r, cz-r, h, r*2, r*2, mat)
        else:
            self.box(cx-r, cy-r, cz-h/2, r*2, r*2, h, mat)

    def disc(self, cx, cy, cz, r, th, mat='STEEL'):
        """Horizontal disc (flat cylinder)."""
        self.cyl_v(cx, cy, cz, r, th, mat, seg=20)

    def panel(self, x, y, z, W, D, mat='SOLAR'):
        """Flat horizontal panel."""
        self.box(x, y, z, W, 0.02, D, mat)

    def render(self, vw, vh, bg='#060c1b'):
        """Return complete SVG string."""
        # Sort back to front
        self._parts.sort(key=lambda p: p[0])
        shapes = ''.join(p[1] for p in self._parts)
        grid = ('<defs>'
                '<pattern id="ig" width="24" height="24" patternUnits="userSpaceOnUse">'
                '<path d="M24,0L0,0L0,24" fill="none" stroke="#0c1630" stroke-width="0.5"/>'
                '</pattern></defs>'
                f'<rect width="{vw}" height="{vh}" fill="{bg}"/>'
                f'<rect width="{vw}" height="{vh}" fill="url(#ig)" opacity="0.6"/>')
        return f'<svg viewBox="0 0 {vw} {vh}" xmlns="http://www.w3.org/2000/svg">{grid}{shapes}</svg>'

# ── Callout label renderer ────────────────────────────────────────────────────
def callout_label(n, label, col='#ff8c00'):
    return (f'<div class="il-callout">'
            f'<span class="il-num" style="background:{col}">{n}</span>'
            f'<span class="il-text">{label}</span>'
            f'</div>')

# ── Per-product illustration data ─────────────────────────────────────────────
def make_spray_x():
    iso = ISO(scale=110, cx=220, cy=200)
    # Hub
    iso.box(-0.17,-0.01,-0.17, 0.34,0.18,0.34, 'CARBON')
    iso.box(-0.14, 0.17,-0.14, 0.28,0.04,0.28, 'ALU')
    # 6 arms
    for deg in [0,60,120,180,240,300]:
        a=math.radians(deg); L=0.74; r=0.028
        cx=math.cos(a)*L/2; cz=math.sin(a)*L/2
        iso.box(cx-L/2*math.cos(a),-0.01+0.06, cz-L/2*math.sin(a), L*abs(math.cos(a))+r, 0.06, L*abs(math.sin(a))+r, 'CARBON')
        # motors
        mx=math.cos(a)*0.76; mz=math.sin(a)*0.76
        iso.cyl_v(mx, 0.06, mz, 0.042, 0.055, 'DARK')
        iso.disc(mx, 0.118, mz, 0.16, 0.006, 'CARBON')
    # Tank below
    iso.cyl_v(-0.20,-0.32,-0.15, 0.20,0.22,'HDPE')
    # Boom
    iso.box(-0.82,-0.34,-0.008, 1.64,0.04,0.016, 'ALU')
    # Nozzles
    for nx in [-0.66,-0.44,-0.22,0,0.22,0.44,0.66]:
        iso.cyl_v(nx,-0.40,-0.008, 0.008,0.06,'HDPE')
    labels = [('Chemical Tank','#0088ff'),('Spray Boom','#0088ff'),
              ('Propeller Motor','#00cc88'),('Arm Latch','#ff8c00'),('Radar Altimeter','#ff8c00')]
    return iso, labels

def make_scout():
    iso = ISO(scale=310, cx=230, cy=200)
    iso.box(-0.065,-0.028,-0.065, 0.130,0.060,0.130, 'DARK')
    iso.box(-0.055, 0.032,-0.055, 0.110,0.020,0.110, 'CARBON')
    for deg in [45,135,225,315]:
        a=math.radians(deg); L=0.110; r=0.012
        cx=math.cos(a)*L/2; cz=math.sin(a)*L/2
        iso.box(cx-0.05, 0, cz-0.05, 0.10,0.015,0.10, 'CARBON')
        mx=math.cos(a)*L; mz=math.sin(a)*L
        iso.cyl_v(mx,0.010,mz, 0.016,0.024,'DARK')
        iso.disc(mx,0.030,mz, 0.085,0.004,'CARBON')
    iso.box(-0.025,-0.040,-0.005, 0.050,0.032,0.040, 'DARK')
    iso.cyl_v(-0.002,-0.045,0.028, 0.010,0.020,'PC')
    labels = [('Main Frame','#0088ff'),('Multispectral Camera','#0088ff'),
              ('Folding Arm','#00cc88'),('Propeller','#ff8c00')]
    return iso, labels

def make_nest():
    iso = ISO(scale=68, cx=230, cy=280)
    iso.box(-0.60,-0.70,-0.60, 1.20,0.10,1.20,'STEEL')
    for face,(px,pz,W,D) in enumerate([( 0.56,-0.60,0.04,1.20),(-0.60,-0.60,0.04,1.20),
                                        (-0.60, 0.56,1.20,0.04),(-0.60,-0.60,1.20,0.04)]):
        iso.box(px,-0.60,pz, W,1.30,D,'ALU')
    iso.box(-0.44,0.60,-0.57, 0.88,0.04,1.14,'ALU')
    iso.box( 0.00,0.60,-0.57, 0.88,0.04,1.14,'ALU')
    iso.box(-0.60,0.54,-0.58, 0.88,0.04,0.30,'DARK')
    iso.panel(-0.44,0.60,-0.44, 0.88,0.88,'DARK')
    iso.box(-0.58,-0.10,-0.55, 0.30,0.80,0.82,'DARK')
    labels = [('Retractable Roof','#0088ff'),('Drone Landing Pad','#00cc88'),
              ('Battery Magazine','#ff8c00'),('HVAC Unit','#ff8c00')]
    return iso, labels

def make_watchtower():
    iso = ISO(scale=28, cx=200, cy=300)
    iso.box(-0.25,-0.20,-0.25, 0.50,0.30,0.50,'CONC')
    iso.cyl_v(-0.02, 0.10,-0.02, 0.038,5.20,'STEEL')
    iso.box( 0.04,3.10, 0.00, 0.28,0.20,0.16,'DARK')
    iso.panel(-0.04,4.54, 0.26, 0.68,0.44,'SOLAR')
    iso.cyl_v(-0.02,5.24,-0.02, 0.095,0.13,'DARK')
    iso.disc(-0.02,5.38,-0.02, 0.130,0.06,'PC')
    iso.cyl_v( 0.04,5.50,-0.02, 0.007,0.36,'ALU')
    iso.cyl_v(-0.04,5.45,-0.02, 0.005,0.26,'ALU')
    labels = [('PTZ Camera Dome','#0088ff'),('Solar Panel','#00cc88'),
              ('LTE Antenna','#ff8c00'),('AI Enclosure','#ff8c00')]
    return iso, labels

def make_soilnode():
    iso = ISO(scale=560, cx=240, cy=240)
    iso.cyl_v(-0.002, 0,-0.002, 0.046,0.15,'HDPE')
    iso.disc(-0.002,0.152,-0.002, 0.046,0.010,'SOLAR')
    iso.cyl_v(-0.002,-0.005,-0.002, 0.046,0.018,'ALU')
    iso.cyl_v(-0.002,-0.110,-0.002, 0.022,0.200,'STEEL')
    for deg in [0,120,240]:
        a=math.radians(deg)
        iso.cyl_v(math.cos(a)*0.016-0.002,-0.200,math.sin(a)*0.016-0.002, 0.003,0.065,'GREEN')
    labels = [('Solar Dome Cap','#0088ff'),('ABS Electronics Housing','#0088ff'),
              ('Threaded Seal','#00cc88'),('NPK Probes','#ff8c00')]
    return iso, labels

def make_feedpro():
    iso = ISO(scale=56, cx=240, cy=300)
    iso.box(-0.46,-0.06,-0.34, 0.92,0.30,0.68,'DARK')
    # frame uprights
    for px,pz in [(-0.44,-0.32),(-0.44,0.30),(0.44,-0.32),(0.44,0.30)]:
        iso.cyl_v(px,-0.06,pz, 0.018,1.90,'STEEL')
    # Dry feed hopper
    iso.box(-0.44, 0.78,-0.28, 0.46,0.60,0.54,'HDPE')
    iso.box(-0.44, 0.50,-0.24, 0.38,0.18,0.44,'HDPE')
    iso.box(-0.44, 1.38,-0.28, 0.48,0.04,0.56,'ALU')
    # Bird trough
    iso.box(-0.78, 0.30,-0.28, 0.22,0.10,0.56,'ALU')
    # Aqua feed hopper (right)
    iso.cyl_v(0.24, 0.60,-0.002, 0.175,0.76,'HDPE')
    iso.disc(0.24, 1.36,-0.002, 0.185,0.04,'ALU')
    # Broadcaster
    iso.cyl_v(0.24, 1.50,-0.002, 0.016,0.28,'STEEL')
    iso.disc(0.24, 1.686,-0.002, 0.19,0.018,'STEEL')
    # Water arm
    iso.cyl_v(0.44, 0.24,-0.002, 0.014,0.88,'STEEL')
    iso.cyl_h(0.44, 1.05, 0.16, 0.012,0.36,'z','STEEL')
    iso.cyl_v(0.44,1.04, 0.40, 0.020,0.06,'ALU')
    # Solar
    iso.panel(-0.46, 1.76,-0.30, 0.90,0.60,'SOLAR')
    # Control module
    iso.box( 0.28, 0.70, 0.21, 0.18,0.22,0.06,'DARK')
    iso.box( 0.28, 0.72, 0.268, 0.11,0.12,0.005,'SCREEN')
    labels = [('Dry-Feed Hopper (Birds)','#0088ff'),('Bird Trough','#0088ff'),
              ('Aqua-Feed Hopper (Fish)','#00cc88'),('Pellet Broadcaster Disc','#00cc88'),
              ('Water Dispenser Arm','#ff8c00'),('Solar Array','#ff8c00'),
              ('Touchscreen Control','#cc44ff')]
    return iso, labels

def make_herdtag():
    iso = ISO(scale=1800, cx=240, cy=210)
    iso.box(-0.024,-0.0075,-0.018, 0.048,0.015,0.036,'TPU')
    iso.box(-0.018,-0.0040,-0.012, 0.036,0.008,0.026,'DARK')
    iso.box(-0.016,-0.0020,-0.010, 0.032,0.003,0.022,'GREEN')
    iso.cyl_v(-0.002, 0.010,-0.002, 0.0030,0.018,'STEEL')
    iso.cyl_v(-0.002,-0.014,-0.002, 0.0025,0.016,'STEEL')
    labels = [('TPU Overmould Body','#0088ff'),('PCB Assembly','#0088ff'),
              ('Piercing Pin','#ff8c00'),('TPU Sheath','#00cc88')]
    return iso, labels

def make_aquasense():
    iso = ISO(scale=145, cx=240, cy=240)
    # Torus approximated as ring of boxes
    for deg in range(0,360,18):
        a=math.radians(deg); R=0.20; r=0.09
        cx2=math.cos(a)*R; cz2=math.sin(a)*R
        iso.box(cx2-r*0.6,-0.09,cz2-r*0.6, r*1.2,0.18,r*1.2,'HDPE')
    iso.panel(-0.19, 0.10,-0.19, 0.38,0.38,'SOLAR')
    iso.box(-0.046, 0.06,-0.046, 0.092,0.050,0.092,'DARK')
    iso.cyl_v(-0.002,-0.06,-0.002, 0.055,0.26,'ALU')
    iso.cyl_h(-0.044,-0.17,-0.002, 0.008,0.10,'x','STEEL')
    iso.cyl_h(-0.002,-0.17,-0.044, 0.008,0.10,'x','STEEL')
    iso.cyl_h( 0.040,-0.17,-0.002, 0.008,0.10,'x','STEEL')
    iso.cyl_v(-0.002,-0.38,-0.002, 0.075,0.055,'LEAD')
    labels = [('Float Hull (HDPE)','#0088ff'),('Solar Panel Array','#00cc88'),
              ('Probe Cage + Sensors','#ff8c00'),('Ballast Module','#ff8c00')]
    return iso, labels

def make_fencegrid():
    iso = ISO(scale=420, cx=220, cy=200)
    iso.box(-0.090,-0.029,-0.055, 0.180,0.058,0.110,'PC')
    for x in [-0.030,0.030]:
        iso.box(x,-0.027,-0.053, 0.004,0.054,0.106,'DARK')
    iso.disc(-0.002, 0.030,-0.002, 0.024,0.008,'PC')
    iso.box(-0.070, 0.022, 0.052, 0.140,0.010,0.004,'SOLAR')
    iso.box(-0.090,-0.042,-0.006, 0.100,0.012,0.080,'STEEL')
    labels = [('Polycarbonate Housing','#0088ff'),('Antenna Radome','#0088ff'),
              ('Solar Strip','#00cc88'),('U-Bolt Mounting Bracket','#ff8c00')]
    return iso, labels

def make_hub():
    iso = ISO(scale=130, cx=240, cy=200)
    iso.box(-0.210,-0.080,-0.160, 0.420,0.160,0.320,'DARK')
    iso.box(-0.180,-0.080,-0.128, 0.360,0.010,0.256,'ALU')
    for x in range(-6,7,2):
        iso.cyl_v(x*0.028,-0.064,-0.160, 0.006,0.060,'ALU')
    for y in range(3):
        iso.box(-0.216,-0.040+y*0.028,-0.150, 0.008,0.016,0.012,'DARK')
    iso.box(-0.106,-0.080,-0.170, 0.212,0.160,0.012,'DARK')
    labels = [('Aluminium Chassis','#0088ff'),('Antenna Array','#0088ff'),
              ('Industrial I/O Ports','#00cc88'),('Cooling Vents','#ff8c00')]
    return iso, labels

def make_crewlink():
    iso = ISO(scale=1200, cx=240, cy=210)
    iso.box(-0.0325,-0.009,-0.022, 0.065,0.018,0.045,'TPU')
    iso.box(-0.026,-0.005,-0.018, 0.052,0.008,0.036,'DARK')
    iso.box(-0.020,-0.003,-0.014, 0.040,0.010,0.028,'SCREEN')
    iso.cyl_v( 0.022,0.004,-0.010, 0.005,0.006,'ORANGE')
    iso.cyl_v(-0.002, 0.010,-0.010, 0.004,0.010,'ALU')
    labels = [('TPU Overmould','#0088ff'),('E-Ink Display','#0088ff'),
              ('SOS Button','#ff4444'),('LoRa Antenna','#00cc88')]
    return iso, labels

def make_agrimule():
    iso = ISO(scale=38, cx=240, cy=240)
    # Tracks
    iso.box(-1.20,-0.24,-0.78, 2.40,0.28,0.20,'RUBBER')
    iso.box(-1.20,-0.24, 0.58, 2.40,0.28,0.20,'RUBBER')
    # Body
    iso.box(-0.76, 0.04,-0.64, 1.52,0.88,1.28,'ALU')
    iso.box(-0.56, 0.14,-0.44, 1.12,0.52,0.88,'DARK')
    # LiDAR
    iso.cyl_v(-0.002, 0.54,-0.002, 0.070,0.060,'DARK')
    iso.disc(-0.002, 0.60,-0.002, 0.075,0.016,'DARK')
    # Solar
    iso.panel(-0.54, 0.96,-0.44, 1.08,0.88,'SOLAR')
    # Tow hitch
    iso.box(-1.25,-0.04,-0.08, 0.10,0.14,0.16,'STEEL')
    labels = [('LiDAR Puck','#0088ff'),('Solar Charging Panel','#00cc88'),
              ('Rubber Track Assembly','#ff8c00'),('Tow Hitch','#ff8c00')]
    return iso, labels

def make_rowplanter():
    iso = ISO(scale=12, cx=240, cy=200)
    # Main toolbar beam (very wide)
    iso.box(-3.0, 0.60,-0.16, 6.0,0.14,0.32,'STEEL')
    # 8 row units
    for i in range(8):
        x = -3.0 + 0.75 + i*0.86
        iso.box(x-0.08,-0.40,-0.18, 0.16,1.00,0.36,'DARK')
        iso.box(x-0.10, 0.54,-0.20, 0.20,0.12,0.40,'GREEN')
        iso.disc(x,-0.42,-0.002, 0.12,0.04,'STEEL')
    # Hydraulic lines
    iso.box(-2.90, 0.70,-0.02, 5.80,0.04,0.04,'DARK')
    labels = [('Main Toolbar Beam','#0088ff'),('Electric Seed Meter','#00cc88'),
              ('Closing Wheel','#ff8c00'),('Hydraulic Lines','#ff8c00')]
    return iso, labels

def make_terraplanter():
    iso = ISO(scale=20, cx=240, cy=260)
    # Wheels (4)
    for px,pz in [(-1.0,0.0),( 1.0,0.0),(-1.0,-0.80),( 1.0,-0.80)]:
        iso.disc(px,-0.38,pz, 0.24,0.14,'RUBBER')
    # Body
    iso.box(-0.88, 0.00,-0.70, 1.76,0.88,0.70,'ALU')
    iso.box(-0.64, 0.10,-0.50, 1.28,0.60,0.50,'DARK')
    # Hydraulic arm
    iso.cyl_v(0.80, 0.88,-0.34, 0.040,0.90,'STEEL')
    iso.box( 0.56, 1.76,-0.20, 0.50,0.12,0.40,'STEEL')
    iso.box( 0.80, 1.84,-0.24, 0.14,0.22,0.22,'DARK')
    # Rotary magazine
    iso.disc(-0.002, 1.00,-0.34, 0.20,0.04,'ORANGE')
    labels = [('Hydraulic Auger Arm','#0088ff'),('Rotary Sapling Magazine','#00cc88'),
              ('4WD Chassis','#ff8c00'),('Cab + Control Unit','#ff8c00')]
    return iso, labels

def make_microweeder():
    iso = ISO(scale=42, cx=240, cy=240)
    # Outer frame
    iso.box(-0.80, 0.10,-0.60, 0.06,0.80,0.06,'STEEL')
    iso.box( 0.74, 0.10,-0.60, 0.06,0.80,0.06,'STEEL')
    iso.box(-0.80, 0.10, 0.54, 0.06,0.80,0.06,'STEEL')
    iso.box( 0.74, 0.10, 0.54, 0.06,0.80,0.06,'STEEL')
    # Top rails
    iso.box(-0.78, 0.90,-0.58, 1.56,0.06,0.06,'STEEL')
    iso.box(-0.78, 0.90, 0.50, 1.56,0.06,0.06,'STEEL')
    # Delta arms
    for ax,az in [(-0.46,-0.002),(0.44,-0.002)]:
        iso.cyl_v(ax, 0.52,-0.002, 0.020,0.32,'ALU')
    iso.cyl_v(-0.002, 0.52,-0.002, 0.020,0.32,'ALU')
    # Platform + laser head
    iso.box(-0.16, 0.06,-0.12, 0.32,0.20,0.24,'DARK')
    iso.disc(-0.002, 0.04,-0.002, 0.06,0.04,'RED')
    # Camera
    iso.box(-0.10, 0.52,-0.02, 0.20,0.10,0.14,'DARK')
    labels = [('50W Fiber Laser Head','#ff4444'),('High-Speed Vision Camera','#0088ff'),
              ('Delta Robot Arms','#00cc88'),('Gantry Frame','#ff8c00')]
    return iso, labels

def make_brushcrusher():
    iso = ISO(scale=18, cx=240, cy=230)
    # Main frame
    iso.box(-1.90, 0.02,-1.04, 3.80,0.80,2.08,'STEEL')
    # Mulcher drum (front)
    for i in range(12):
        ang=math.radians(i*30)
        iso.box(-1.72+i*0.30,-0.04,-1.00, 0.18,0.28,2.00,'DARK')
    iso.cyl_h(-1.86, 0.12,-0.002, 0.28,3.72,'x','DARK')
    # Teeth
    for xi in range(14):
        for zi in range(3):
            iso.box(-1.86+xi*0.27, 0.34,-0.90+zi*0.58, 0.10,0.14,0.10,'YELLOW')
    # Hydraulic motor
    iso.disc(1.72, 0.12,-0.002, 0.18,0.10,'DARK')
    # Deflector shield
    iso.box(-1.90, 0.82,-1.04, 3.80,0.08,2.08,'STEEL')
    # 3-point hitch
    iso.box(1.92,-0.06,-0.40, 0.12,0.70,0.80,'STEEL')
    labels = [('Tungsten Carbide Teeth','#f0c020'),('Front Drum Mulcher','#0088ff'),
              ('Steel Deflector Shield','#00cc88'),('Hydraulic Drive Motor','#ff8c00')]
    return iso, labels

def make_omniharvester():
    iso = ISO(scale=19, cx=240, cy=280)
    # Wheels (4 large)
    for px,pz in [(-1.20,0.08),(1.20,0.08),(-1.20,-1.18),(1.20,-1.18)]:
        iso.disc(px,-0.38,pz, 0.24,0.32,'RUBBER')
    # Main body
    iso.box(-1.14, 0.02,-1.06, 2.28,3.00,1.06,'ALU')
    iso.box(-0.88, 0.12,-0.84, 1.76,2.60,0.84,'DARK')
    # Conveyor belt (center bottom)
    iso.box(-1.08, 0.00,-0.52, 2.16,0.08,0.96,'RUBBER')
    # Arm pairs (3 × each side)
    for k in range(3):
        iso.box( 1.12, 0.30+k*0.72,-0.44, 0.22,0.16,0.88,'GREEN')
        iso.box(-1.34, 0.30+k*0.72,-0.44, 0.22,0.16,0.88,'GREEN')
        iso.disc(1.32, 0.38+k*0.72,-0.002, 0.12,0.04,'ALU')
        iso.disc(-1.36,0.38+k*0.72,-0.002, 0.12,0.04,'ALU')
    # Stereo cameras on front face
    for xi in range(3):
        iso.box(-0.66+xi*0.62, 2.42,-0.53, 0.14,0.09,0.09,'DARK')
    labels = [('Soft-Grip End Effectors','#00cc88'),('Stereo Vision Cameras','#0088ff'),
              ('Central Conveyor Belt','#0088ff'),('4WD Wheel Assembly','#ff8c00')]
    return iso, labels

PRODUCT_FUNCS = [
    ('01','01_spray_x.html',    make_spray_x,    'UAV-01  ·  Hexacopter Spray Drone'),
    ('02','02_scout.html',      make_scout,      'UAV-02  ·  Folding Scout Quadrotor'),
    ('03','03_nest.html',       make_nest,       'INF-01  ·  Drone Docking Station'),
    ('04','04_watchtower.html', make_watchtower, 'INF-02  ·  AI Monitoring Pole'),
    ('05','05_soilnode.html',   make_soilnode,   'SNS-01  ·  In-Ground Soil Sensor'),
    ('06','06_feedpro.html',    make_feedpro,    'SYS-01  ·  Multi-Species Feeding Station'),
    ('07','07_herdtag.html',    make_herdtag,    'SNS-02  ·  Livestock Ear Tag'),
    ('08','08_aquasense.html',  make_aquasense,  'SNS-03  ·  Water Quality Buoy'),
    ('09','09_fencegrid.html',  make_fencegrid,  'SNS-04  ·  Perimeter Sensor Node'),
    ('10','10_hub.html',        make_hub,        'SYS-02  ·  Edge AI Gateway Hub'),
    ('11','11_crewlink.html',   make_crewlink,   'W-01   ·  Crew Wearable Device'),
    ('12','12_agrimule.html',   make_agrimule,   'M-01   ·  Autonomous Field Robot'),
    ('13','13_rowplanter.html', make_rowplanter, 'I-01   ·  Row Crop Planting Implement'),
    ('14','14_terraplanter.html',make_terraplanter,'I-02  ·  Sapling Transplanting Machine'),
    ('15','15_microweeder.html',make_microweeder,'R-01   ·  Precision Laser Weeder'),
    ('16','16_brushcrusher.html',make_brushcrusher,'R-02  ·  Mulching / Brush Crusher'),
    ('17','17_omniharvester.html',make_omniharvester,'H-01  ·  Autonomous Harvester Robot'),
]

# ── CSS for the illustration section ─────────────────────────────────────────
ILLUS_CSS = """
  <style id="illus-css">
    .illus-section { margin: 28px 0 0; }
    .illus-section h2 { margin-bottom: 14px; }
    .illus-wrap {
      display: grid;
      grid-template-columns: 1fr 320px;
      gap: 0;
      border: 1px solid #1b2f5e;
      border-radius: 8px;
      overflow: hidden;
      background: #060c1b;
    }
    .illus-svg-panel svg { display: block; width: 100%; height: auto; }
    .illus-labels-panel {
      background: #080e20;
      border-left: 1px solid #1b2f5e;
      padding: 24px 20px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .illus-product-cat {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9px;
      letter-spacing: 0.18em;
      color: #2a4888;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    .il-callout {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 6px 0;
      border-bottom: 1px solid #0e1a36;
    }
    .il-callout:last-child { border-bottom: none; }
    .il-num {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      font-family: 'JetBrains Mono', monospace;
      font-size: 9px;
      font-weight: 700;
      color: #fff;
      flex-shrink: 0;
    }
    .il-text {
      font-family: 'Inter', sans-serif;
      font-size: 11px;
      color: #8aaccc;
      line-height: 1.4;
    }
  </style>
"""

def build_illus_html(prod_id, cat_label, iso, labels):
    svg_str = iso.render(520, 380)
    labels_html = ''
    for i,(label,col) in enumerate(labels, 1):
        labels_html += callout_label(i, label, col)
    return (
        f'\n  <section class="illus-section">\n'
        f'    <h2>Product Illustration</h2>\n'
        f'    <div class="illus-wrap">\n'
        f'      <div class="illus-svg-panel">{svg_str}</div>\n'
        f'      <div class="illus-labels-panel">\n'
        f'        <div class="illus-product-cat">{cat_label}</div>\n'
        f'        {labels_html}\n'
        f'      </div>\n'
        f'    </div>\n'
        f'  </section>\n'
    )

# ── Update each HTML file ────────────────────────────────────────────────────
for prod_id, filename, func, cat_label in PRODUCT_FUNCS:
    path = os.path.join(BASE, filename)
    with open(path, encoding='utf-8') as f:
        html = f.read()

    # Inject CSS if not present
    if 'illus-css' not in html:
        html = html.replace('</head>', ILLUS_CSS + '</head>', 1)

    # Build illustration
    iso, labels = func()
    illus_html = build_illus_html(prod_id, cat_label, iso, labels)

    # Replace or insert illus-section after views-section (or after first </section>)
    if '<section class="illus-section">' in html:
        html = re.sub(r'<section class="illus-section">.*?</section>\n',
                      illus_html.strip() + '\n', html, flags=re.DOTALL, count=1)
    else:
        # Insert after the views-section closing tag, or after first </section> if no views-section
        if '</section>\n\n  <div class="grid' in html:
            html = html.replace(
                '</section>\n\n  <div class="grid',
                '</section>\n' + illus_html + '\n  <div class="grid',
                1
            )
        else:
            # fallback: insert after views-section
            html = re.sub(r'(</section>)(\s*\n\s*<div class="grid)',
                          lambda m: m.group(1) + illus_html + m.group(2),
                          html, count=1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓  {filename}")

print(f"\nDone. {len(PRODUCT_FUNCS)} illustrations generated.")
