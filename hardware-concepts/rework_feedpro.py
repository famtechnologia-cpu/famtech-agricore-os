#!/usr/bin/env python3
"""
Rework Feedpro as a multi-species automated feeding station
(birds/poultry dry feed + fish aqua-pellet broadcaster + water dispensing arm)
then re-embed the new GLB into 06_feedpro.html and update all spec content.
"""
import sys, os, re, base64, numpy as np

sys.path.insert(0, os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages"))
from pygltflib import (GLTF2, Scene, Node, Mesh, Primitive, Accessor,
                        BufferView, Buffer, Asset, Material,
                        PbrMetallicRoughness, Attributes)

BASE = "/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts"
OUT  = f"{BASE}/models"

# ── Materials ─────────────────────────────────────────────────────────────────
ALU    = (0.80, 0.82, 0.86, 0.92, 0.12)
STEEL  = (0.52, 0.54, 0.58, 0.88, 0.28)
HDPE   = (0.92, 0.91, 0.87, 0.00, 0.88)
PC     = (0.87, 0.92, 0.96, 0.04, 0.08)
SOLAR  = (0.04, 0.06, 0.24, 0.55, 0.14)
SOLAR2 = (0.02, 0.04, 0.18, 0.65, 0.10)
DARK   = (0.11, 0.12, 0.14, 0.28, 0.55)
ORANGE = (0.92, 0.34, 0.04, 0.00, 0.40)
GREEN  = (0.04, 0.72, 0.50, 0.12, 0.36)
RUBBER = (0.06, 0.06, 0.06, 0.00, 0.96)
LED_G  = (0.05, 0.95, 0.45, 0.00, 0.40, 0.0, 3.0, 1.0)
LED_B  = (0.05, 0.25, 0.95, 0.00, 0.40, 0.0, 0.5, 4.0)
SCREEN = (0.12, 0.16, 0.22, 0.05, 0.20, 0.1, 0.2, 0.5)
WATER  = (0.10, 0.50, 0.90, 0.04, 0.10, 0.0, 0.3, 0.8)  # water pipe tint

_BI = np.array([0,1,2,0,2,3,5,4,7,5,7,6,4,0,3,4,3,7,
                1,5,6,1,6,2,0,4,5,0,5,1,3,2,6,3,6,7], dtype=np.uint32)

def box(cx,cy,cz,w,h,d):
    x0,x1=cx-w/2,cx+w/2; y0,y1=cy-h/2,cy+h/2; z0,z1=cz-d/2,cz+d/2
    v=np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
                [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],dtype=np.float32)
    return v,_BI.copy()

def cyl(cx,cy,cz,r,h,seg=24,axis='y'):
    a=np.linspace(0,2*np.pi,seg,endpoint=False)
    c1,c2=np.cos(a)*r,np.sin(a)*r
    if axis=='y':
        bot=np.c_[c1,np.full(seg,-h/2),c2]; top=np.c_[c1,np.full(seg,h/2),c2]
        bc=np.array([[0,-h/2,0]]); tc=np.array([[0,h/2,0]])
    elif axis=='x':
        bot=np.c_[np.full(seg,-h/2),c1,c2]; top=np.c_[np.full(seg,h/2),c1,c2]
        bc=np.array([[-h/2,0,0]]); tc=np.array([[h/2,0,0]])
    else:
        bot=np.c_[c1,c2,np.full(seg,-h/2)]; top=np.c_[c1,c2,np.full(seg,h/2)]
        bc=np.array([[0,0,-h/2]]); tc=np.array([[0,0,h/2]])
    v=np.vstack([bot,top,bc,tc]).astype(np.float32)
    bi,ti=seg*2,seg*2+1
    idx=[]
    for i in range(seg):
        j=(i+1)%seg
        idx+=[i,j,seg+j,i,seg+j,seg+i,bi,j,i,ti,seg+i,seg+j]
    v[:,0]+=cx; v[:,1]+=cy; v[:,2]+=cz
    return v,np.array(idx,dtype=np.uint32)

def dome(cx,cy,cz,r,seg=20):
    vs,idx=[],[]
    rings=seg//2
    for ri in range(rings+1):
        phi=(np.pi/2)*ri/rings; y=np.sin(phi)*r; rc=np.cos(phi)*r
        for ai in range(seg):
            ang=2*np.pi*ai/seg
            vs.append([np.cos(ang)*rc,y,np.sin(ang)*rc])
    top=len(vs); vs.append([0,r,0])
    for ri in range(rings):
        for ai in range(seg):
            a0=ri*seg+ai; a1=ri*seg+(ai+1)%seg
            b0=(ri+1)*seg+ai; b1=(ri+1)*seg+(ai+1)%seg
            if ri<rings-1: idx+=[a0,a1,b1,a0,b1,b0]
            else: idx+=[a0,a1,top]
    v=np.array(vs,dtype=np.float32); v[:,0]+=cx; v[:,1]+=cy; v[:,2]+=cz
    return v,np.array(idx,dtype=np.uint32)

def solar_panel(cx,cy,cz,W,D,rows=4,cols=6):
    parts=[(box(cx,cy,cz,W,0.006,D))]
    cw=(W-0.008*(cols+1))/cols; ch=(D-0.008*(rows+1))/rows
    for r in range(rows):
        for c in range(cols):
            px=cx-W/2+0.008*(c+1)+cw*(c+0.5)
            pz=cz-D/2+0.008*(r+1)+ch*(r+0.5)
            parts.append(box(px,cy+0.003,pz,cw,0.004,ch))
    vs,ix=[],[]; off=0
    for v,i in parts:
        vs.append(v); ix.append(i+off); off+=len(v)
    return np.vstack(vs),np.concatenate(ix)

def merge(parts):
    vs,ix=[],[]; off=0
    for v,i in parts:
        vs.append(v); ix.append(i+off); off+=len(v)
    return np.vstack(vs),np.concatenate(ix)

# ── GLB Builder ───────────────────────────────────────────────────────────────
class B:
    def __init__(self):
        self.g=GLTF2()
        self.g.asset=Asset(version="2.0",generator="Famtech AgriCore v2")
        self.g.scenes=[Scene(name="Scene",nodes=[])]; self.g.scene=0
        self.g.nodes=[]; self.g.meshes=[]
        self.g.accessors=[]; self.g.bufferViews=[]
        self.g.materials=[]; self.g.buffers=[Buffer(byteLength=0)]
        self._blob=bytearray(); self._mc={}
    def _mat(self,c):
        key=tuple(round(x,4) for x in c)
        if key not in self._mc:
            i=len(self.g.materials)
            r,g,b=c[0],c[1],c[2]
            metal=c[3] if len(c)>3 else 0.3
            rough=c[4] if len(c)>4 else 0.6
            emit=[c[5],c[6],c[7]] if len(c)>7 else [0.0,0.0,0.0]
            self.g.materials.append(Material(
                pbrMetallicRoughness=PbrMetallicRoughness(
                    baseColorFactor=[r,g,b,1.0],
                    metallicFactor=metal,roughnessFactor=rough),
                emissiveFactor=emit,doubleSided=True))
            self._mc[key]=i
        return self._mc[key]
    def _push(self,arr,tgt):
        pad=(4-len(self._blob)%4)%4; self._blob+=b'\x00'*pad
        off=len(self._blob); blob=arr.tobytes(); self._blob+=blob
        bv=len(self.g.bufferViews)
        self.g.bufferViews.append(BufferView(buffer=0,byteOffset=off,byteLength=len(blob),target=tgt))
        return bv
    def _acc(self,arr,ct,at,tgt):
        bv=self._push(arr,tgt)
        mn=arr.min(0).tolist() if arr.ndim>1 else [float(arr.min())]
        mx=arr.max(0).tolist() if arr.ndim>1 else [float(arr.max())]
        i=len(self.g.accessors)
        self.g.accessors.append(Accessor(bufferView=bv,byteOffset=0,
            componentType=ct,count=len(arr),type=at,min=mn,max=mx))
        return i
    def part(self,name,v,i,mat=STEEL):
        if len(i)==0: return
        pa=self._acc(v.astype(np.float32),5126,"VEC3",34962)
        ia=self._acc(i.astype(np.uint32).flatten(),5125,"SCALAR",34963)
        mi=self._mat(mat)
        msh=len(self.g.meshes)
        self.g.meshes.append(Mesh(name=name,primitives=[
            Primitive(attributes=Attributes(POSITION=pa),indices=ia,material=mi,mode=4)]))
        n=len(self.g.nodes)
        self.g.nodes.append(Node(name=name,mesh=msh))
        self.g.scenes[0].nodes.append(n)
    def save(self,path):
        self.g.buffers[0].byteLength=len(self._blob)
        self.g.set_binary_blob(bytes(self._blob))
        self.g.save_binary(path)
        print(f"  ✓  {os.path.basename(path)}")

# ═══════════════════════════════════════════════════════════════════════════════
#  Feedpro V2 — Multi-Species Automated Feeding Station  960×680×1950 mm
#  Supports: Poultry/Birds (dry feed + trough), Fish (aqua-pellets + broadcaster),
#            Aquaculture (water dispenser arm + flow metering)
# ═══════════════════════════════════════════════════════════════════════════════
def build_feedpro_v2():
    b = B()

    # ── Main structural frame (powder-coated steel uprights + cross-beams) ──
    for px,pz in [(-0.44,-0.32),(-0.44,0.32),(0.44,-0.32),(0.44,0.32)]:
        b.part(f"Frame_Upright_{px:.2f}_{pz:.2f}", *cyl(px,-0.04,pz, 0.018,1.90), STEEL)
    # Horizontal rails at 3 heights
    for hy in [-0.04, 0.34, 1.10]:
        b.part(f"Rail_Front_{hy:.2f}", *cyl(0,hy,-0.32, 0.012,0.88, axis='x'), STEEL)
        b.part(f"Rail_Rear_{hy:.2f}",  *cyl(0,hy, 0.32, 0.012,0.88, axis='x'), STEEL)
    # Base plate
    b.part("Base_Plate",              *box(0,-0.06,0, 0.92,0.04,0.66), STEEL)

    # ── Battery & electronics bay (bottom sealed cabinet) ──────────────────
    b.part("Battery_Bay_Housing",     *box(0, 0.14,0, 0.86,0.30,0.60), DARK)
    b.part("Battery_Bay_Door",        *box(-0.26,0.14,0.305, 0.32,0.28,0.008), ALU)
    b.part("Battery_Vent_Grille",     *merge([box(-0.26+j*0.028,0.14,0.305, 0.010,0.16,0.004)
                                               for j in range(8)]), DARK)
    b.part("Electronics_Module",      *box(0.20,0.14,-0.005, 0.26,0.22,0.54), DARK)

    # ── Left wing: Dry-Feed Hopper (for poultry / birds) ───────────────────
    # Large HDPE hopper — tapered from top lid to auger chute
    b.part("Dry_Feed_Hopper_Upper",   *box(-0.22, 1.08, 0, 0.46, 0.60, 0.54), HDPE)
    b.part("Dry_Feed_Hopper_Taper",   *merge([
        box(-0.22,0.68,0, 0.38,0.18,0.44),
        box(-0.22,0.54,0, 0.26,0.14,0.30),
    ]), HDPE)
    b.part("Dry_Feed_Hopper_Lid",     *box(-0.22, 1.40, 0, 0.48, 0.04, 0.56), ALU)
    b.part("Lid_Hinge",               *cyl(-0.22,1.42,0.27, 0.010,0.48, axis='x'), STEEL)
    b.part("Hopper_Level_Window",     *box(-0.42, 1.02, 0, 0.008, 0.30, 0.10), PC)
    b.part("Hopper_Status_LED",       *cyl(-0.38,1.30,0.10, 0.006,0.005), LED_G)

    # Auger drive (horizontal, feeds into bird trough)
    b.part("Auger_Tube",              *cyl(-0.22,0.46,0, 0.032,0.72, seg=18, axis='x'), ALU)
    b.part("Auger_Drive_Motor",       *box(-0.52,0.44,0, 0.14,0.12,0.12), DARK)
    b.part("Motor_Fins",              *merge([box(-0.54+j*0.014,0.44,0, 0.005,0.10,0.10)
                                               for j in range(5)]), ALU)

    # Bird Trough (stainless, extends left)
    b.part("Bird_Trough_Arm",         *cyl(-0.47,0.45,0, 0.012,0.06, axis='x'), STEEL)
    b.part("Bird_Trough_Body",        *box(-0.66,0.34,0, 0.22,0.10,0.56), ALU)
    b.part("Bird_Trough_Drain",       *cyl(-0.66,0.28,0, 0.014,0.04), ALU)
    # Trough perch rod
    b.part("Perch_Rod",               *cyl(-0.66,0.44,0, 0.006,0.58, axis='z'), STEEL)

    # ── Right wing: Aqua-Feed Hopper (fish pellets) ─────────────────────────
    b.part("Aqua_Feed_Hopper",        *cyl(0.24, 0.98, 0, 0.175, 0.72, seg=20), HDPE)
    b.part("Aqua_Hopper_Lid",         *cyl(0.24, 1.36, 0, 0.185, 0.04, seg=20), ALU)
    b.part("Aqua_Hopper_Window",      *box(0.40, 0.98, 0, 0.008, 0.40, 0.08), PC)
    b.part("Aqua_Feed_Outlet_Pipe",   *cyl(0.24, 0.60, 0, 0.025, 0.16), HDPE)

    # Pellet Broadcaster (spinning disc for fish pond scatter feeding)
    b.part("Broadcaster_Mast",        *cyl(0.24, 1.50, 0, 0.016, 0.28), STEEL)
    b.part("Broadcaster_Motor_Hub",   *cyl(0.24, 1.66, 0, 0.038, 0.050), DARK)
    b.part("Broadcaster_Disc",        *cyl(0.24, 1.686, 0, 0.190, 0.018, seg=28), STEEL)
    b.part("Disc_Vanes",              *merge([
        box(0.24+np.cos(a)*0.09, 1.695, np.sin(a)*0.09, 0.04, 0.010, 0.025)
        for a in np.linspace(0, 2*np.pi, 6, endpoint=False)
    ]), ALU)

    # ── Water Dispenser Arm (for fish tank / bird drinkers) ─────────────────
    b.part("Water_Vertical_Pipe",     *cyl(0.44, 0.60, 0, 0.014, 0.88), STEEL)
    b.part("Water_Elbow",             *cyl(0.44, 1.05, 0, 0.018, 0.040), ALU)
    b.part("Water_Horizontal_Arm",    *cyl(0.44, 1.05, 0.20, 0.012, 0.40, axis='z'), STEEL)
    b.part("Flow_Meter_Housing",      *box(0.44, 1.03, 0.24, 0.044, 0.060, 0.044), DARK)
    b.part("Flow_Meter_Window",       *box(0.44, 1.05, 0.24, 0.020, 0.020, 0.016), PC)
    b.part("Dispenser_Nozzle",        *cyl(0.44, 1.05, 0.42, 0.020, 0.065, axis='z'), ALU)
    b.part("Nozzle_Valve_Ring",       *cyl(0.44, 1.05, 0.40, 0.026, 0.018, axis='z'), ORANGE)
    b.part("Water_Supply_Inlet",      *cyl(0.44, 0.14, 0, 0.020, 0.10, axis='z'), STEEL)

    # ── Solar array on top ────────────────────────────────────────────────
    b.part("Solar_Panel_Frame",       *box(-0.04, 1.76, 0, 0.92, 0.030, 0.60), ALU)
    b.part("Solar_Panel_Array",       *solar_panel(-0.04, 1.78, 0, 0.86, 0.54, rows=3, cols=6), SOLAR)
    b.part("Solar_Cell_Grid",         *solar_panel(-0.04, 1.793, 0, 0.82, 0.50, rows=3, cols=6), SOLAR2)
    b.part("Solar_Tilt_Bracket",      *merge([cyl(px, 1.68, 0, 0.012, 0.18)
                                               for px in [-0.36, 0.28]]), STEEL)

    # ── Control Module (weatherproof touchscreen) ─────────────────────────
    b.part("Control_Module_Body",     *box(0.38, 0.80, 0.25, 0.18, 0.22, 0.06), DARK)
    b.part("Touchscreen_Display",     *box(0.38, 0.82, 0.276, 0.11, 0.12, 0.005), SCREEN)
    b.part("Control_Bezel",           *box(0.38, 0.82, 0.274, 0.13, 0.14, 0.006), DARK)
    b.part("Power_Button",            *cyl(0.36, 0.72, 0.276, 0.009, 0.006, axis='z'), ORANGE)
    b.part("Status_LED_Array",        *merge([cyl(0.39+j*0.015, 0.72, 0.276, 0.004, 0.004, axis='z')
                                               for j in range(3)]), LED_G)
    b.part("USB_Port",                *box(0.28, 0.76, 0.277, 0.016, 0.010, 0.004), DARK)

    # ── Connectivity (LoRa + WiFi antennas) ──────────────────────────────
    b.part("LoRa_Antenna",            *cyl(0.40, 1.78, 0, 0.006, 0.28), ALU)
    b.part("WiFi_Antenna",            *cyl(0.33, 1.78, 0, 0.005, 0.20), ALU)
    b.part("Antenna_Base",            *box(0.365, 1.76, 0, 0.10, 0.010, 0.020), DARK)

    # ── Load cell mounts (4-point weighing platform) ─────────────────────
    for px,pz in [(-0.40,-0.28),(0.40,-0.28),(-0.40,0.28),(0.40,0.28)]:
        b.part(f"Load_Cell_{px:.2f}_{pz:.2f}",
               *merge([cyl(px,-0.08,pz, 0.028,0.05),
                        box(px,-0.11,pz, 0.08,0.020,0.055),
                        box(px,-0.14,pz, 0.06,0.014,0.040)]), STEEL)

    b.save(f"{OUT}/feedpro.glb")

# ── Run ───────────────────────────────────────────────────────────────────────
print("Building Feedpro V2 — Multi-Species Feeding Station…")
build_feedpro_v2()

# ── Re-embed into HTML ────────────────────────────────────────────────────────
glb_path = f"{OUT}/feedpro.glb"
html_path = f"{BASE}/06_feedpro.html"

with open(glb_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
data_uri = f"data:model/gltf-binary;base64,{b64}"

with open(html_path, encoding="utf-8") as f:
    html = f.read()

# Replace GLB data URI
html = re.sub(r'src="data:model/gltf-binary;base64,[^"]*"',
              f'src="{data_uri}"', html, count=1)

# Update hotspot positions for new geometry
html = html.replace(
    'slot="hotspot-0" data-position="0.000 0.900 0.000" data-normal="0.0 1.0 0.0"',
    'slot="hotspot-0" data-position="-0.22 1.40 0.000" data-normal="0.0 1.0 0.0"'
)
html = html.replace(
    'slot="hotspot-1" data-position="0.440 0.000 0.000" data-normal="1.0 0.0 0.0"',
    'slot="hotspot-1" data-position="0.44 1.05 0.420" data-normal="0.0 0.0 1.0"'
)
html = html.replace(
    'slot="hotspot-2" data-position="0.320 0.320 0.320" data-normal="0.0 0.0 1.0"',
    'slot="hotspot-2" data-position="0.24 1.686 0.000" data-normal="0.0 1.0 0.0"'
)
html = html.replace(
    'slot="hotspot-3" data-position="0.400 -0.740 -0.280" data-normal="0.0 -1.0 0.0"',
    'slot="hotspot-3" data-position="0.38 0.80 0.277" data-normal="0.0 0.0 1.0"'
)

# ── Update all spec content in the HTML ──────────────────────────────────────
UPDATES = [
    # Product description
    (r'Automated solar or mains-powered livestock and aquaculture feeding system with load-cell monitoring\.',
     'Multi-species automated dispensing station for poultry/birds, aquaculture (fish), and bird drinkers — solar-powered with load-cell precision dosing and real-time consumption telemetry.'),
    # IP badge
    ('badge-neutral">IP54', 'badge-neutral">IP65'),
    # Stats
    ('<span class="stat-label">Power</span><span class="stat-value">Mains</span>',
     '<span class="stat-label">Power</span><span class="stat-value">Solar + Mains</span>'),
    # Dimensions
    ('850 × 620 × 1480 mm', '960 × 680 × 1950 mm'),
    # Ground clearance
    ('100 mm', '120 mm'),
    # Sensor suite row
    ('<tr><th>Sensor Suite</th><td>Load Cells, Auger RPM</td></tr>',
     '<tr><th>Sensor Suite</th><td>4× Load Cells, Flow Meter, Hopper Level</td></tr>'),
    # Connectivity (add MQTT)
    ('<tr><th>Connectivity</th><td>Wi-Fi, LoRa</td></tr>',
     '<tr><th>Connectivity</th><td>Wi-Fi 6, LoRa, MQTT Cloud</td></tr>'),
    # IP row
    ('<tr><th>Ingress Protection</th><td>IP54</td></tr>',
     '<tr><th>Ingress Protection</th><td>IP65 (waterproof)</td></tr>'),
    # Form factor
    ('<span class="brief-value">Standing Cabinet</span>',
     '<span class="brief-value">Multi-Bay Feeding Station</span>'),
    # Role
    ('<span class="brief-value">Automated Feeding</span>',
     '<span class="brief-value">Multi-Species Auto-Dispensing</span>'),
    # Mechanical arch
    ('Gravity-fed hopper into horizontal auger tube, 12V planetary gearbox motor',
     'Dual-hopper system: left = dry-feed auger (poultry/birds), right = aqua-pellet cylinder + spinning broadcaster disc; independent water dispenser arm with flow meter'),
    # Materials
    ('Food-grade HDPE hopper, powder-coated steel frame, stainless steel auger',
     'IP65 food-grade HDPE hoppers, 316L stainless steel trough and water arm, powder-coated carbon steel frame, UV-stable polycarbonate inspection windows'),
    # Component map chips
    ('<div class="comp-grid"><span class="comp-chip">Feed Hopper</span><span class="comp-chip">Auger Assembly</span><span class="comp-chip">Motor Drive</span><span class="comp-chip">Load Cell Mounts</span></div>',
     '<div class="comp-grid">'
     '<span class="comp-chip">Dry-Feed Hopper (Birds)</span>'
     '<span class="comp-chip">Auger Drive + Bird Trough</span>'
     '<span class="comp-chip">Aqua-Feed Hopper (Fish)</span>'
     '<span class="comp-chip">Pellet Broadcaster Disc</span>'
     '<span class="comp-chip">Water Dispenser Arm</span>'
     '<span class="comp-chip">Flow Meter</span>'
     '<span class="comp-chip">Solar Panel Array</span>'
     '<span class="comp-chip">Load Cell Platform</span>'
     '<span class="comp-chip">Touchscreen Control</span>'
     '</div>'),
    # Fusion build sequence
    ('<ul class="fusion-list"><li>Steel_Frame</li><li>Hopper_Tub</li><li>Auger_Drive</li><li>Control_Box</li></ul>',
     '<ul class="fusion-list">'
     '<li>Frame_Uprights → Rail_Structure</li>'
     '<li>Battery_Bay_Housing</li>'
     '<li>Dry_Feed_Hopper_Upper → Auger_Tube</li>'
     '<li>Bird_Trough_Body</li>'
     '<li>Aqua_Feed_Hopper → Broadcaster_Disc</li>'
     '<li>Water_Vertical_Pipe → Water_Horizontal_Arm → Dispenser_Nozzle</li>'
     '<li>Solar_Panel_Array</li>'
     '<li>Control_Module_Body → Touchscreen_Display</li>'
     '<li>Load_Cell_Mounts</li>'
     '</ul>'),
    # Risks
    ('<ul class="risk-list"><li>Feed bridging in humid climates</li><li>Rodent damage</li><li>Motor stall</li></ul>',
     '<ul class="risk-list">'
     '<li>Aqua-pellet moisture absorption blocking outlet</li>'
     '<li>Broadcaster disc clogging with wet feed in high humidity</li>'
     '<li>Water arm freezing in sub-zero deployment</li>'
     '<li>Algae growth in water dispenser tubing</li>'
     '<li>Bird nesting on trough perch rod obstructing sensors</li>'
     '</ul>'),
    # Annotation callouts
    ('<div class="ann-list"><span class="ann-tag">Hopper Lid</span><span class="ann-tag">Auger Output</span><span class="ann-tag">Control Box</span></div>',
     '<div class="ann-list">'
     '<span class="ann-tag">Dry-Feed Hopper Lid</span>'
     '<span class="ann-tag">Aqua-Feed Cylinder</span>'
     '<span class="ann-tag">Pellet Broadcaster Disc</span>'
     '<span class="ann-tag">Water Nozzle Valve</span>'
     '<span class="ann-tag">Bird Trough</span>'
     '<span class="ann-tag">Touchscreen Control Module</span>'
     '<span class="ann-tag">Solar Panel Array</span>'
     '</div>'),
    # Manufacturing notes
    ('Rotomolded hopper, welded box-tube steel frame, sheet metal guards',
     'HDPE hoppers rotomolded (food-grade), 316L stainless trough and water circuits, powder-coat steel frame, ASA weather-resistant control enclosure, IP65 cable glands on all penetrations'),
    # Maintenance
    ('<div class="panel"><p>Feed bridging in humid climates. Rotomolded hopper, welded box-tube steel frame, sheet metal guards</p></div>',
     '<div class="panel"><p>Weekly: flush water arm with clean water cycle. Monthly: inspect broadcaster disc vanes for wear, clean aqua-feed outlet. Quarterly: calibrate load cells, inspect solar panel connections and cable glands.</p></div>'),
]

for old, new in UPDATES:
    html = html.replace(old, new)

# Also add new spec rows for species coverage
html = html.replace(
    '<tr><th>Power System</th><td>Mains</td></tr>',
    '<tr><th>Power System</th><td>Solar Primary + Mains Backup</td></tr>'
    '<tr><th>Species</th><td>Poultry, Birds, Fish, Aquaculture</td></tr>'
)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"  ✓  06_feedpro.html updated ({len(b64)//1024} KB GLB embedded)")
print("Feedpro V2 complete.")
