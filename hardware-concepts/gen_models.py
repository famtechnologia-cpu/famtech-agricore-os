#!/usr/bin/env python3
"""
Famtech AgriCore — realistic GLB generator v2.
Full PBR materials (metallic/roughness/emissive), high-poly geometry,
detailed components, and proper proportions per spec.
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages"))
from pygltflib import (GLTF2, Scene, Node, Mesh, Primitive, Accessor,
                        BufferView, Buffer, Asset, Material,
                        PbrMetallicRoughness, Attributes)

OUT = "/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts/models"
os.makedirs(OUT, exist_ok=True)

# ── Materials  (r,g,b, metallic, roughness[, emit_r,emit_g,emit_b]) ──────────
# Tuple length 5 = opaque, 8 = with emissive
ALU    = (0.80, 0.82, 0.86, 0.92, 0.12)   # polished aluminium
STEEL  = (0.52, 0.54, 0.58, 0.88, 0.28)   # brushed steel
CARBON = (0.06, 0.06, 0.07, 0.08, 0.30)   # carbon fibre weave
HDPE   = (0.92, 0.91, 0.87, 0.00, 0.88)   # food-grade white HDPE
PC     = (0.87, 0.92, 0.96, 0.04, 0.08)   # polycarbonate dome
SOLAR  = (0.04, 0.06, 0.24, 0.55, 0.14)   # dark solar panel glass
RUBBER = (0.06, 0.06, 0.06, 0.00, 0.96)   # rubber tracks/tyres
TPU    = (0.54, 0.40, 0.10, 0.00, 0.74)   # TPU overmould
ORANGE = (0.92, 0.34, 0.04, 0.00, 0.40)   # powder-coat orange
GREEN  = (0.04, 0.72, 0.50, 0.12, 0.36)   # Famtech green
DARK   = (0.11, 0.12, 0.14, 0.28, 0.55)   # dark anodised electronics
LEAD   = (0.28, 0.29, 0.33, 0.62, 0.44)   # cast lead ballast
CONC   = (0.54, 0.51, 0.48, 0.00, 0.92)   # concrete anchor
RED    = (0.85, 0.10, 0.10, 0.00, 0.42)   # red accent
YELLOW = (0.92, 0.82, 0.04, 0.00, 0.36)   # yellow teeth / warning
SOLAR2 = (0.02, 0.04, 0.18, 0.65, 0.10)   # solar cell (extra sheen)
PCB_G  = (0.05, 0.28, 0.12, 0.10, 0.60)   # PCB green
# Emissive materials (8-element)
LED_G  = (0.05, 0.95, 0.45, 0.00, 0.40,  0.0, 3.0, 1.0)
LED_R  = (0.95, 0.08, 0.08, 0.00, 0.40,  3.5, 0.0, 0.0)
LED_B  = (0.05, 0.25, 0.95, 0.00, 0.40,  0.0, 0.5, 4.0)
SCREEN = (0.12, 0.16, 0.22, 0.05, 0.20,  0.1, 0.2, 0.5)

# ── Geometry helpers ──────────────────────────────────────────────────────────
_BI = np.array([0,1,2,0,2,3,5,4,7,5,7,6,4,0,3,4,3,7,
                1,5,6,1,6,2,0,4,5,0,5,1,3,2,6,3,6,7], dtype=np.uint32)

def box(cx,cy,cz,w,h,d):
    x0,x1=cx-w/2,cx+w/2; y0,y1=cy-h/2,cy+h/2; z0,z1=cz-d/2,cz+d/2
    v=np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
                [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],dtype=np.float32)
    return v,_BI.copy()

def rbox(cx,cy,cz,L,H,D,ay=0.0):
    v=np.array([[-L/2,-H/2,-D/2],[L/2,-H/2,-D/2],[L/2,H/2,-D/2],[-L/2,H/2,-D/2],
                [-L/2,-H/2,D/2],[L/2,-H/2,D/2],[L/2,H/2,D/2],[-L/2,H/2,D/2]],dtype=np.float32)
    if ay:
        ca,sa=np.cos(ay),np.sin(ay)
        x_=v[:,0]*ca+v[:,2]*sa; z_=-v[:,0]*sa+v[:,2]*ca
        v[:,0]=x_; v[:,2]=z_
    v[:,0]+=cx; v[:,1]+=cy; v[:,2]+=cz
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
    else:  # z
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

def rcyl(cx,cy,cz,r,h,ay=0.0,seg=24):
    """Cylinder along X, rotated around Y, then translated."""
    v,inds=cyl(0,0,0,r,h,seg, axis='x')
    if ay:
        ca,sa=np.cos(ay),np.sin(ay)
        x_=v[:,0]*ca+v[:,2]*sa; z_=-v[:,0]*sa+v[:,2]*ca
        v[:,0]=x_; v[:,2]=z_
    v[:,0]+=cx; v[:,1]+=cy; v[:,2]+=cz
    return v,inds

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

def sphere(cx,cy,cz,r,seg=20):
    """Full UV sphere."""
    vs,idx=[],[]
    rings=seg//2
    for ri in range(rings+1):
        phi=np.pi*ri/rings-np.pi/2; y=np.sin(phi)*r; rc=np.cos(phi)*r
        for ai in range(seg):
            ang=2*np.pi*ai/seg
            vs.append([np.cos(ang)*rc,y,np.sin(ang)*rc])
    bot=len(vs); vs.append([0,-r,0])
    top=len(vs); vs.append([0, r,0])
    for ri in range(rings):
        for ai in range(seg):
            a0=ri*seg+ai; a1=ri*seg+(ai+1)%seg
            b0=(ri+1)*seg+ai; b1=(ri+1)*seg+(ai+1)%seg
            if ri==0: idx+=[bot,a1,a0]
            elif ri==rings-1: idx+=[a0,a1,top]
            else: idx+=[a0,a1,b1,a0,b1,b0]
    v=np.array(vs,dtype=np.float32); v[:,0]+=cx; v[:,1]+=cy; v[:,2]+=cz
    return v,np.array(idx,dtype=np.uint32)

def torus(cx,cy,cz,R,r,seg=28,tube=14):
    """Torus in XZ plane."""
    vs,idx=[],[]
    for i in range(seg):
        a=2*np.pi*i/seg; ca,sa=np.cos(a),np.sin(a)
        for j in range(tube):
            b=2*np.pi*j/tube; cb,sb=np.cos(b),np.sin(b)
            x=(R+r*cb)*ca; y=r*sb; z=(R+r*cb)*sa
            vs.append([x,y,z])
    for i in range(seg):
        for j in range(tube):
            a0=i*tube+j; a1=i*tube+(j+1)%tube
            b0=((i+1)%seg)*tube+j; b1=((i+1)%seg)*tube+(j+1)%tube
            idx+=[a0,a1,b1,a0,b1,b0]
    v=np.array(vs,dtype=np.float32); v[:,0]+=cx; v[:,1]+=cy; v[:,2]+=cz
    return v,np.array(idx,dtype=np.uint32)

def solar_panel(cx,cy,cz,W,D,rows=4,cols=6):
    """Solar panel with visible cell grid lines."""
    parts=[]
    # backing slab
    parts.append(box(cx,cy,cz,W,0.016,D))
    # cell grid — horizontal rails
    for r in range(rows+1):
        z=cz-D/2+r*D/rows
        parts.append(box(cx,cy+0.008,z, W,0.003,0.003))
    # vertical dividers
    for c in range(cols+1):
        x=cx-W/2+c*W/cols
        parts.append(box(x,cy+0.008,cz, 0.003,0.003,D))
    return merge(parts)

def merge(parts):
    vs,ix=[],[]; off=0
    for v,i in parts:
        vs.append(v); ix.append(i+off); off+=len(v)
    return np.vstack(vs),np.concatenate(ix)

# ── GLB builder ───────────────────────────────────────────────────────────────
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
                    metallicFactor=metal,
                    roughnessFactor=rough),
                emissiveFactor=emit,
                doubleSided=True))
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
#  01  Spray X  — Hexacopter UAV  2180×760×690 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_spray_x():
    b=B()
    # Central hub — octagonal body
    b.part("Central_Core_Hub",  *box(0,0.06,0, 0.36,0.14,0.36), CARBON)
    b.part("Hub_Top_Cap",       *box(0,0.14,0, 0.32,0.025,0.32), ALU)
    b.part("Hub_Bottom_Plate",  *box(0,-0.01,0, 0.34,0.015,0.34), ALU)
    b.part("Avionics_Deck",     *box(0,0.17,0, 0.24,0.03,0.24), DARK)
    b.part("GPS_Antenna",       *cyl(0.08,0.20,0.08, 0.018,0.022), DARK)

    # 6 arms as cylinders at 60° intervals
    arm_L=0.78
    for k,deg in enumerate([0,60,120,180,240,300]):
        a=np.radians(deg)
        cx=np.cos(a)*arm_L/2; cz=np.sin(a)*arm_L/2
        b.part(f"Arm_{k+1}",        *rcyl(cx,0.06,cz, 0.030,arm_L,ay=-a), CARBON)
        b.part(f"Arm_Motor_Mount_{k+1}",*cyl(np.cos(a)*arm_L,0.08,np.sin(a)*arm_L, 0.045,0.035), ALU)
        mx=np.cos(a)*arm_L; mz=np.sin(a)*arm_L
        b.part(f"Motor_{k+1}",      *cyl(mx,0.115,mz, 0.040,0.050), DARK)
        b.part(f"Motor_Can_{k+1}",  *cyl(mx,0.130,mz, 0.032,0.025), ALU)
        # Two-blade propeller
        b.part(f"Propeller_{k+1}",  *merge([rbox(mx,0.145,mz, 0.340,0.004,0.028,ay=-a),
                                              rbox(mx,0.145,mz, 0.340,0.004,0.028,ay=-a+np.pi/2)]), CARBON)
    # Folding arm latches (visible orange rings at fold points)
    for deg in [0,60,120,180,240,300]:
        a=np.radians(deg)
        lx=np.cos(a)*0.19; lz=np.sin(a)*0.19
        b.part(f"Folding_Arm_Latch_{deg}",*cyl(lx,0.06,lz, 0.038,0.030), ORANGE)

    # Quick-swap tank bay
    b.part("Quick-swap_Tank_Bay",*box(0,-0.17,0, 0.44,0.28,0.28), HDPE)
    b.part("Tank_Fill_Cap",      *cyl(0.12,-0.02,0, 0.028,0.040), ALU)
    b.part("Tank_Level_Window",  *box(0.20,-0.17,0, 0.008,0.18,0.04), PC)

    # Spray boom
    b.part("Spray_Boom_Array",   *rcyl(0,-0.33,0, 0.016,1.60), ALU)
    b.part("Boom_Pipe_L",        *rcyl(-0.55,-0.32,0, 0.010,0.60,ay=0), HDPE)
    b.part("Boom_Pipe_R",        *rcyl( 0.55,-0.32,0, 0.010,0.60,ay=0), HDPE)
    # Nozzles — 8 total
    for nx in np.linspace(-0.70,0.70,8):
        b.part(f"Nozzle_{nx:.2f}", *cyl(nx,-0.38,0, 0.010,0.035), HDPE)
    b.part("Flow_Control_Valve", *cyl(0,-0.33,0.14, 0.022,0.055), ALU)
    b.part("Radar_Altimeter",    *box(0,-0.04,0.15, 0.060,0.030,0.050), DARK)

    # Landing gear (3 legs at 120°)
    for deg in [90,210,330]:
        a=np.radians(deg)
        fx=np.cos(a)*0.42; fz=np.sin(a)*0.42
        b.part(f"Landing_Leg_{deg}",*merge([
            rcyl(np.cos(a)*0.22,-0.05,np.sin(a)*0.22, 0.012,0.44,ay=-a+np.pi/2),
            box(fx,-0.24,fz, 0.02,0.30,0.02),
            box(fx,-0.40,fz, 0.08,0.014,0.05)
        ]), CARBON)

    b.save(f"{OUT}/spray_x.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  02  Scout  — Folding Quadrotor  340×340×110 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_scout():
    b=B()
    b.part("Main_Frame",        *box(0,0,0, 0.130,0.055,0.130), DARK)
    b.part("Top_Shell",         *box(0,0.032,0, 0.110,0.018,0.110), CARBON)
    b.part("Battery_Door",      *box(0,-0.028,0, 0.090,0.006,0.070), ALU)
    b.part("USB_Port",          *box(0.066,-0.010,0, 0.010,0.010,0.018), DARK)

    for k,deg in enumerate([45,135,225,315]):
        a=np.radians(deg)
        L=0.110
        cx=np.cos(a)*L/2; cz=np.sin(a)*L/2
        b.part(f"Folding_Arm_{k+1}",   *rcyl(cx,0,cz, 0.014,L,ay=-a), CARBON)
        b.part(f"Folding_Pivot_{k+1}", *cyl(np.cos(a)*0.052,0.004,np.sin(a)*0.052, 0.011,0.028), ORANGE)
        mx=np.cos(a)*L; mz=np.sin(a)*L
        b.part(f"Motor_{k+1}",         *cyl(mx,0.012,mz, 0.017,0.022), DARK)
        b.part(f"Motor_Bell_{k+1}",    *cyl(mx,0.020,mz, 0.014,0.016), ALU)
        # Propeller (two-blade)
        b.part(f"Propeller_{k+1}",     *merge([
            rbox(mx,0.028,mz, 0.180,0.003,0.016,ay=-a),
            rbox(mx,0.028,mz, 0.180,0.003,0.016,ay=-a+np.pi/2)]), CARBON)
    # Gimbal + camera
    b.part("Gimbal_Module",     *cyl(0,-0.040,0, 0.028,0.032), DARK)
    b.part("Gimbal_Roll_Arm",   *rcyl(0,-0.038,0, 0.005,0.060), ALU)
    b.part("Multispectral_Array",*box(0,-0.060,0.010, 0.048,0.030,0.038), DARK)
    b.part("Camera_Lens_RGB",   *cyl(0,-0.060,0.030, 0.012,0.018, axis='z'), PC)
    b.part("Camera_Lens_MS",    *cyl(-0.014,-0.060,0.030, 0.008,0.014, axis='z'), PC)
    b.part("Vision_Sensors",    *merge([box(0.012,-0.060,0.030, 0.009,0.009,0.012),
                                         box(-0.012,-0.060,0.030, 0.009,0.009,0.012)]), DARK)
    b.part("Cooling_Intake",    *box(0,0.028,0.066, 0.048,0.012,0.008), ALU)
    b.part("Status_LED",        *cyl(0.042,0.006,0.060, 0.004,0.004), LED_G)
    b.save(f"{OUT}/scout.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  03  Nest  — Drone Docking Station  1200×1200×1400 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_nest():
    b=B()
    # Base slab
    b.part("Base_Frame",         *box(0,-0.65,0, 1.20,0.10,1.20), STEEL)
    b.part("Ground_Anchor_Bolts",*merge([cyl(x,-0.72,z, 0.020,0.14)
                                          for x,z in [(-0.55,-0.55),(-0.55,0.55),(0.55,-0.55),(0.55,0.55)]]), STEEL)
    # Four shell walls (painted aluminium panels)
    for face,(px,pz,W,D) in enumerate([( 0, 0.60,1.20,0.04),( 0,-0.60,1.20,0.04),
                                        ( 0.60, 0,0.04,1.20),(-0.60, 0,0.04,1.20)]):
        b.part(f"Shell_Panel_{face+1}", *box(px,0.12,pz, W,1.24,D), ALU)
    # Roof — two sliding halves with visible seam gap
    b.part("Retractable_Roof_L", *box(-0.305,0.755,0, 0.585,0.040,1.18), ALU)
    b.part("Retractable_Roof_R", *box( 0.305,0.755,0, 0.585,0.040,1.18), ALU)
    b.part("Roof_Rail_L",        *cyl(0,0.740,-0.58, 0.016,1.16, axis='z'), STEEL)
    b.part("Roof_Rail_R",        *cyl(0,0.740, 0.58, 0.016,1.16, axis='z'), STEEL)
    b.part("Roof_Actuator_L",    *cyl(-0.56,0.35,0, 0.022,0.64), STEEL)
    b.part("Roof_Actuator_R",    *cyl( 0.56,0.35,0, 0.022,0.64), STEEL)
    # Landing pad with alignment markers
    b.part("Drone_Landing_Pad",  *box(0,0.560,0, 0.88,0.024,0.88), DARK)
    b.part("Landing_Alignment_Cross",*merge([
        box(0,0.574,0, 0.70,0.004,0.04),
        box(0,0.574,0, 0.04,0.004,0.70),
        cyl(0,0.574,0, 0.12,0.005, axis='y')]), ORANGE)
    # Battery magazine
    b.part("Battery_Magazine",   *box(-0.40,-0.10,0, 0.30,0.80,0.82), DARK)
    b.part("Battery_Slot_Faces", *merge([box(-0.555,-0.10+j*0.22,0, 0.006,0.16,0.72)
                                          for j in range(4)]), ALU)
    # Robotic swap arm
    b.part("Robotic_Swap_Arm",   *merge([cyl(0.10,0.16,0, 0.030,0.80),
                                          cyl(0.10,0.56,0, 0.025,0.40, axis='z'),
                                          cyl(0.10,0.58,0.20, 0.022,0.06)]), GREEN)
    # HVAC unit
    b.part("HVAC_Unit",          *box(0.66,0.02,0, 0.076,0.44,0.44), STEEL)
    b.part("HVAC_Vent",          *merge([box(0.700,0.02+j*0.06,0, 0.010,0.030,0.36)
                                          for j in range(6)]), DARK)
    b.part("Status_Panel",       *box(0.58,-0.42,0, 0.060,0.120,0.240), DARK)
    b.part("Status_LEDs",        *merge([cyl(0.57,-0.36+j*0.04,0.08, 0.007,0.004)
                                          for j in range(4)]), LED_G)
    b.save(f"{OUT}/nest.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  04  Watchtower  — Monitoring Pole  780×780×6000 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_watchtower():
    b=B()
    b.part("Concrete_Anchor",    *box(0,-0.16,0, 0.50,0.32,0.50), CONC)
    b.part("Base_Flange",        *box(0,0.01,0, 0.22,0.024,0.22), STEEL)
    # Mast in 3 sections with flanges
    for k,(y0,h) in enumerate([(0.02,1.60),(1.64,1.60),(3.26,1.60)]):
        b.part(f"Mast_Section_{k+1}",*cyl(0,y0+h/2,0, 0.038,h), STEEL)
        b.part(f"Mast_Flange_{k+1}", *box(0,y0+h+0.008,0, 0.090,0.020,0.090), STEEL)
    b.part("Mast_Top_Section",   *cyl(0,5.30,0, 0.030,0.80), STEEL)

    # Solar panel assembly
    b.part("Solar_Bracket",      *merge([box(0.04,4.66,0.26, 0.040,0.040,0.52),
                                          box(0,4.64,0.52, 0.080,0.016,0.01)]), STEEL)
    b.part("Solar_Panel_Mount",  *solar_panel(0,4.68,0.54, 0.64,0.44, rows=4,cols=6), SOLAR)
    b.part("Solar_Cell_Grid",    *solar_panel(0,4.690,0.54, 0.60,0.40, rows=4,cols=6), SOLAR2)

    # AI enclosure on mast
    b.part("AI_Enclosure",       *box(0.12,3.20,0, 0.260,0.200,0.160), DARK)
    b.part("Enclosure_Fins",     *merge([box(0.22+j*0.018,3.20,0, 0.006,0.180,0.140)
                                          for j in range(4)]), ALU)
    b.part("Enclosure_Status_LED",*cyl(0.10,3.30,0.082, 0.006,0.005), LED_G)
    b.part("Enclosure_Hinges",   *merge([cyl(-0.01, 3.26, -0.084, 0.006, 0.040, axis='z'), 
                                          cyl(-0.01, 3.14, -0.084, 0.006, 0.040, axis='z')]), STEEL)
    b.part("Enclosure_Latches",  *merge([box(0.25, 3.26, 0.084, 0.020, 0.030, 0.006), 
                                          box(0.25, 3.14, 0.084, 0.020, 0.030, 0.006)]), STEEL)
    b.part("Cable_Conduit",      *cyl(0.12, 3.96, 0.10, 0.010, 1.20), RUBBER)

    # Antennas
    b.part("LTE_Antenna",        *cyl( 0.06,5.55,0, 0.007,0.360), ALU)
    b.part("LoRa_Antenna",       *cyl(-0.06,5.50,0, 0.005,0.260), ALU)
    b.part("GPS_Puck",           *cyl(0,5.72,0, 0.038,0.018), DARK)

    # PTZ camera pod
    b.part("PTZ_Camera_Pod",     *cyl(0,5.30,0, 0.095,0.130), DARK)
    b.part("PTZ_Dome",           *dome(0,5.36,0, 0.130), PC)
    b.part("Thermal_Camera_Body",*box(0.07,5.29,0.08, 0.044,0.040,0.054), DARK)
    b.part("Camera_Lens_RGB",    *cyl(0,5.29,0.118, 0.022,0.030, axis='z'), PC)
    b.part("Camera_Rain_Hood",   *box(0.07,5.32,0.11, 0.060,0.004,0.080), STEEL)

    b.save(f"{OUT}/watchtower.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  05  Soilnode  — In-Ground Sensor  92×92×310 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_soilnode():
    b=B()
    # Aboveground ABS body
    b.part("ABS_Housing",        *cyl(0,0.075,0, 0.044,0.150,seg=16), HDPE)
    b.part("Housing_Rib_Band",   *cyl(0,0.100,0, 0.048,0.018,seg=16), ALU)
    b.part("Solar_Dome_Cap",     *dome(0,0.152,0, 0.046,seg=20), SOLAR)
    b.part("Solar_Lens",         *dome(0,0.154,0, 0.040,seg=20), PC)
    b.part("Status_LED",         *cyl(0.030,0.110,0.040, 0.005,0.005), LED_G)
    b.part("Electronics_Cartridge",*cyl(0,0.060,0, 0.036,0.090,seg=16), DARK)
    b.part("PCB_Ring",           *cyl(0,0.062,0, 0.034,0.004,seg=16), PCB_G)

    # Threaded seal collar
    b.part("Threaded_Seal",      *cyl(0,-0.005,0, 0.046,0.018,seg=16), ALU)
    b.part("Dual_O_Rings",       *merge([torus(0,0.008,0, 0.046,0.002,seg=20,tube=6),
                                          torus(0,0.014,0, 0.046,0.002,seg=20,tube=6)]), RUBBER)
    b.part("Housing_Grip_Ribs",  *merge([box(np.cos(a)*0.044, 0.050, np.sin(a)*0.044, 0.004, 0.060, 0.004)
                                          for a in np.linspace(0, 2*np.pi, 12, endpoint=False)]), DARK)
    b.part("Extraction_Handle",  *merge([cyl(-0.015,0.105,0, 0.003,0.010,axis='x'),
                                          cyl( 0.015,0.105,0, 0.003,0.010,axis='x'),
                                          cyl(0,0.110,0, 0.003,0.034,axis='z')]), STEEL)

    # Stainless probe below ground
    b.part("Steel_Probe",        *cyl(0,-0.105,0, 0.022,0.200), STEEL)
    b.part("Probe_Taper",        *cyl(0,-0.220,0, 0.012,0.060), STEEL)

    # NPK sensing electrodes (3 thin rods)
    for ang in [0,120,240]:
        a=np.radians(ang)
        px=np.cos(a)*0.016; pz=np.sin(a)*0.016
        b.part(f"NPK_Probe_{ang}",*cyl(px,-0.200,pz, 0.003,0.060), GREEN)
    b.part("Moisture_Ring_Sensor",*cyl(0,-0.160,0, 0.026,0.008,seg=20), GREEN)

    b.save(f"{OUT}/soilnode.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  06  Feedpro  — Automated Feeder  850×620×1480 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_feedpro():
    b=B()
    # Frame
    b.part("Steel_Frame",        *box(0,-0.04,0, 0.86,1.34,0.62), STEEL)
    b.part("Frame_Trim",         *merge([box(x,-0.04,z, 0.02,1.34,0.02)
                                          for x,z in [(-0.43,-0.31),(-0.43,0.31),(0.43,-0.31),(0.43,0.31)]]), DARK)
    # Feed hopper (truncated cone shape)
    b.part("Feed_Hopper",        *box(0,0.60,0, 0.72,0.56,0.52), HDPE)
    b.part("Hopper_Taper",       *box(0,0.24,0, 0.44,0.22,0.34), HDPE)
    b.part("Hopper_Lid",         *box(0,0.90,0, 0.74,0.038,0.54), ALU)
    b.part("Lid_Handle",         *cyl(0,0.935,0, 0.012,0.16,seg=16,axis='z'), STEEL)
    b.part("Hopper_Level_Window",*box(0.355,0.55,0, 0.008,0.30,0.08), PC)

    # Auger tube + motor
    b.part("Auger_Assembly",     *cyl(0,0.00,0, 0.058,0.68,seg=20,axis='x'), ALU)
    b.part("Auger_Housing",      *box(0,0.00,0, 0.70,0.13,0.13), HDPE)
    b.part("Auger_Output_Spout", *cyl(0.44,0.00,0, 0.040,0.18,seg=16,axis='x'), HDPE)
    b.part("Motor_Drive",        *box(-0.38,-0.02,0, 0.160,0.150,0.150), DARK)
    b.part("Motor_Cooling_Fins", *merge([box(-0.40+j*0.014,-0.02,0, 0.006,0.130,0.130)
                                          for j in range(5)]), ALU)

    # Control box
    b.part("Control_Box",        *box(0.32,0.32,0.32, 0.170,0.210,0.055), DARK)
    b.part("Control_Screen",     *box(0.32,0.34,0.348, 0.110,0.100,0.004), SCREEN)
    b.part("Control_Buttons",    *merge([box(0.30+j*0.030,0.26,0.348, 0.018,0.018,0.004)
                                          for j in range(3)]), ORANGE)

    # Load cell mounts (4 legs with load cells)
    for x,z in [(-0.40,-0.28),(0.40,-0.28),(-0.40,0.28),(0.40,0.28)]:
        b.part(f"Load_Cell_Mount_{x:.1f}_{z:.1f}",
               *merge([cyl(x,-0.70,z, 0.025,0.06),
                        box(x,-0.74,z, 0.080,0.018,0.050)]), STEEL)
    # Legs
    for x,z in [(-0.40,-0.28),(0.40,-0.28),(-0.40,0.28),(0.40,0.28)]:
        b.part(f"Leg_{x:.1f}_{z:.1f}",*cyl(x,-0.56,z, 0.016,0.32), STEEL)

    b.save(f"{OUT}/feedpro.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  07  Herdtag  — Livestock Ear Tag  48×36×15 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_herdtag():
    b=B()
    # Main body — slightly rounded rectangle
    b.part("TPU_Overmold",       *box(0,0,0, 0.048,0.015,0.036), TPU)
    b.part("TPU_Edge_Bevel_L",   *cyl(-0.024,0,0, 0.0075,0.036,seg=16,axis='z'), TPU)
    b.part("TPU_Edge_Bevel_R",   *cyl( 0.024,0,0, 0.0075,0.036,seg=16,axis='z'), TPU)
    b.part("Electronics_Puck",   *box(0,0.001,0, 0.038,0.008,0.026), DARK)
    b.part("PCB_Assembly",       *box(0,0.002,0, 0.032,0.003,0.022), PCB_G)
    b.part("Antenna_Loop",       *merge([box( 0.018,0.003, 0, 0.002,0.003,0.018),
                                          box(-0.018,0.003, 0, 0.002,0.003,0.018)]), DARK)
    b.part("Attachment_Pin",     *cyl(0, 0.012,0, 0.0030,0.018), STEEL)
    b.part("Piercing_Pin",       *cyl(0,-0.012,0, 0.0025,0.016), STEEL)
    b.part("TPU_Sheath",         *cyl(0, 0, 0, 0.0055,0.024), TPU)
    b.part("Status_LED",         *cyl(0.018,0.007,0.014, 0.003,0.003), LED_G)
    b.part("Label_Area",         *box(-0.005,0.007,0, 0.020,0.002,0.020), HDPE)
    b.save(f"{OUT}/herdtag.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  08  Aquasense  — Water Quality Buoy  520×520×760 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_aquasense():
    b=B()
    # Torus hull — proper smooth torus
    b.part("Float_Hull",         *torus(0,0,0, 0.20,0.090,seg=28,tube=16), HDPE)
    b.part("Hull_Grip_Wrap",     *torus(0,0,0, 0.20,0.096,seg=28,tube=5), RUBBER)
    b.part("Bumper_Guards",      *merge([box(np.cos(a)*0.28, 0, np.sin(a)*0.28, 0.030,0.160,0.030)
                                          for a in [0, np.pi/2, np.pi, 3*np.pi/2]]), RUBBER)

    # Top solar assembly
    b.part("Solar_Cap_Frame",    *box(0,0.115,0, 0.38,0.024,0.38), ALU)
    b.part("Solar_Panel_Array",  *solar_panel(0,0.128,0, 0.340,0.340, rows=3,cols=4), SOLAR)
    b.part("Solar_Cell_Grid",    *solar_panel(0,0.130,0, 0.330,0.330, rows=3,cols=4), SOLAR2)
    b.part("Solar_Mounting_Bolts", *merge([cyl(x,0.128,z, 0.006,0.006) 
                                            for x in [-0.17,0.17] for z in [-0.17,0.17]]), STEEL)

    # Central mast/hub
    b.part("Central_Hub",        *cyl(0,0.055,0, 0.060,0.130,seg=16), ALU)
    b.part("Electronics_Pod",    *box(0,0.080,0, 0.090,0.050,0.090), DARK)
    b.part("Status_LED_Array",   *merge([cyl(0.046,0.080+j*0.014,0.042, 0.005,0.005)
                                          for j in range(3)]), LED_G)
    b.part("LTE_Antenna",        *cyl(0.040,0.200,0, 0.006,0.160), ALU)

    # Sensor manifold descending
    b.part("Sensor_Manifold",    *cyl(0,-0.060,0, 0.055,0.250,seg=20), ALU)
    b.part("Water_Intake_Grill", *merge([cyl(np.cos(a)*0.055, -0.250, np.sin(a)*0.055, 0.003, 0.180, axis='y') 
                                          for a in np.linspace(0, 2*np.pi, 12, endpoint=False)] +
                                        [torus(0,-0.170,0, 0.055,0.004,seg=20,tube=6),
                                         torus(0,-0.250,0, 0.055,0.004,seg=20,tube=6),
                                         torus(0,-0.330,0, 0.055,0.004,seg=20,tube=6)]), STEEL)
    b.part("Sensor_Array",       *merge([cyl(-0.025,-0.220,0, 0.010,0.120),
                                          cyl( 0.025,-0.220,0, 0.010,0.120),
                                          cyl(0,-0.220,0.025, 0.010,0.120)]), GREEN)
    b.part("DO_Sensor",          *cyl(0,-0.300,0, 0.014,0.080), DARK)
    b.part("pH_Sensor",          *cyl(0.020,-0.290,0, 0.010,0.060), GREEN)
    b.part("Turbidity_Window",   *cyl(0,-0.250,0.040, 0.010,0.030, axis='z'), PC)
    b.part("Ballast_Module",     *cyl(0,-0.370,0, 0.075,0.055), LEAD)
    b.part("Mooring_Ring",       *torus(0,-0.380,0, 0.040,0.007,seg=16,tube=8), STEEL)
    b.part("Grab_Handles",       *merge([box( 0.235,0.040,0, 0.050,0.018,0.025),
                                          box(-0.235,0.040,0, 0.050,0.018,0.025)]), HDPE)
    b.save(f"{OUT}/aquasense.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  09  Fencegrid  — Perimeter Node  180×110×58 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_fencegrid():
    b=B()
    b.part("Main_Housing",       *box(0,0,0, 0.180,0.058,0.110), PC)
    b.part("Housing_Ribs",       *merge([box(x,0,0, 0.004,0.058,0.110)
                                          for x in [-0.060,0,0.060]]), DARK)
    b.part("Front_Cover",        *box(0,0,0.056, 0.176,0.054,0.004), DARK)
    b.part("Rear_Housing",       *box(0,0,-0.056, 0.176,0.054,0.004), DARK)
    b.part("Gasket_Seal",        *merge([box(0,0, 0.053, 0.180,0.058,0.002),
                                          box(0,0,-0.053, 0.180,0.058,0.002)]), RUBBER)
    b.part("Antenna_Radome",     *dome(0,0.034,0, 0.024,seg=16), PC)
    b.part("Solar_Strip",        *box(0,0.026,0.056, 0.140,0.010,0.004), SOLAR)
    b.part("Status_LED",         *cyl(0.072,0.022,0.058, 0.005,0.005), LED_G)
    b.part("IR_Break_Beam_L",    *box(-0.080,0.010,0.040, 0.012,0.012,0.016), DARK)
    b.part("IR_Break_Beam_R",    *box( 0.080,0.010,0.040, 0.012,0.012,0.016), DARK)
    b.part("Vibration_Sensor",   *box(0,-0.010,-0.030, 0.020,0.012,0.012), DARK)
    b.part("U-Bolt_Mount",       *merge([cyl(-0.035,-0.040,0, 0.005,0.044),
                                          cyl( 0.035,-0.040,0, 0.005,0.044),
                                          box(0,-0.062,0, 0.090,0.006,0.012)]), STEEL)
    b.part("Mounting_Bracket",   *box(0,-0.022,0, 0.100,0.012,0.080), STEEL)
    b.save(f"{OUT}/fencegrid.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  10  Hub  — Edge AI Gateway  420×320×160 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_hub():
    b=B()
    # Heatsink chassis body
    b.part("Aluminum_Chassis",   *box(0,0,0, 0.420,0.160,0.320), ALU)
    # Heatsink fins on sides
    b.part("Heatsink_Fins_L",    *merge([box(-0.218+j*0.004,0,0, 0.003,0.140,0.300)
                                          for j in range(8)]), ALU)
    b.part("Heatsink_Fins_R",    *merge([box( 0.210+j*0.004,0,0, 0.003,0.140,0.300)
                                          for j in range(8)]), ALU)
    # Front face panel
    b.part("Steel_Cover_Front",  *box(0,0,0.162, 0.416,0.156,0.006), DARK)
    b.part("Front_Logo_Panel",   *box(0,0.050,0.164, 0.100,0.030,0.002), GREEN)
    # IO panel
    b.part("Industrial_IO",      *box(-0.140,-0.050,0.163, 0.090,0.055,0.003), DARK)
    b.part("Ethernet_Ports",     *merge([box(-0.155+j*0.022,-0.050,0.165, 0.016,0.018,0.004)
                                          for j in range(4)]), DARK)
    b.part("USB_Ports",          *merge([box(-0.060+j*0.020,-0.050,0.165, 0.014,0.010,0.004)
                                          for j in range(2)]), DARK)
    b.part("Power_Inlet",        *box(0.150,-0.050,0.163, 0.030,0.030,0.004), DARK)
    # Rear panel
    b.part("Steel_Cover_Rear",   *box(0,0,-0.162, 0.416,0.156,0.006), STEEL)
    # Antenna array on top
    b.part("Antenna_Array",      *merge([cyl(-0.150,0.110,0, 0.006,0.130),
                                          cyl(-0.080,0.110,0, 0.006,0.110),
                                          cyl( 0.000,0.110,0, 0.006,0.100),
                                          cyl( 0.080,0.110,0, 0.006,0.110),
                                          cyl( 0.150,0.110,0, 0.006,0.130)]), ALU)
    b.part("Cooling_Vents",      *merge([box(0.165,0.040+j*0.028,0.162, 0.028,0.018,0.005)
                                          for j in range(4)]), DARK)
    # Internals (visible when section view)
    b.part("Compute_Board",      *box(0,0.018,0, 0.360,0.080,0.250), PCB_G)
    b.part("UPS_Battery",        *box(0,-0.048,0.060, 0.280,0.060,0.110), DARK)
    b.part("Active_Cooling_Fan_L",*cyl(-0.120,0.060,0, 0.044,0.040), STEEL)
    b.part("Active_Cooling_Fan_R",*cyl( 0.120,0.060,0, 0.044,0.040), STEEL)
    b.part("Wall_Mount_Bracket", *box(0,-0.090,0, 0.380,0.018,0.080), STEEL)
    b.part("Status_LED_Strip",   *merge([cyl(-0.060+j*0.028,0.079,0.164, 0.005,0.003)
                                          for j in range(5)]), LED_G)
    b.save(f"{OUT}/hub.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  11  CrewLink  — Worker Wearable  65×45×18 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_crewlink():
    b=B()
    # Core body with rounded ends
    b.part("Polycarbonate_Core", *box(0,0,0, 0.065,0.018,0.045), PC)
    b.part("Core_End_L",         *cyl(-0.0325,0,0, 0.009,0.045,seg=20,axis='z'), PC)
    b.part("Core_End_R",         *cyl( 0.0325,0,0, 0.009,0.045,seg=20,axis='z'), PC)
    # TPU bumper / shock ring
    b.part("TPU_Bumper",         *merge([box( 0.034,0,0, 0.002,0.020,0.047),
                                          box(-0.034,0,0, 0.002,0.020,0.047),
                                          box(0,0, 0.024, 0.070,0.020,0.002),
                                          box(0,0,-0.024, 0.070,0.020,0.002)]), TPU)
    # Front face
    b.part("E-Ink_Display",      *box(0,0.008,0.016, 0.050,0.002,0.028), SCREEN)
    b.part("Display_Bezel",      *box(0,0.007,0.016, 0.054,0.002,0.032), DARK)
    b.part("SOS_Button",         *cyl(0.036,0,0, 0.0065,0.008), RED)
    b.part("SOS_Button_Guard",   *torus(0.036,0,0, 0.0085,0.002,seg=16,tube=8), ORANGE)
    b.part("Biometric_Window",   *box(0,-0.009,0.010, 0.018,0.003,0.018), PC)
    b.part("Charging_Contacts",  *merge([box(-0.014,-0.009,0, 0.004,0.002,0.006),
                                          box( 0.014,-0.009,0, 0.004,0.002,0.006)]), ALU)
    b.part("Steel_Belt_Clip",    *merge([box(0,-0.013,0, 0.040,0.003,0.032),
                                          box(0,-0.018,0, 0.042,0.008,0.006),
                                          box(0,-0.016,0, 0.026,0.006,0.003)]), STEEL)
    b.part("LoRa_Antenna",       *rbox(0.040,0.004,0, 0.055,0.003,0.002), ALU)
    b.part("Status_LED",         *cyl(-0.036,0.008,0.022, 0.004,0.004), LED_B)
    b.save(f"{OUT}/crewlink.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  12  AgriMule  — Cargo UGV  2400×1500×850 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_agrimule():
    b=B()
    # Main ladder frame
    b.part("Steel_Chassis",      *box(0,0.10,0, 2.00,0.22,1.04), STEEL)
    b.part("Chassis_Cross_Members",*merge([box(x,0.10,0, 0.22,0.16,1.04)
                                            for x in [-0.60,0,0.60]]), STEEL)
    # Tracks — left and right with link approximation
    for side, sz in [(-1,-0.68),(1,0.68)]:
        label='L' if side<0 else 'R'
        b.part(f"Track_Drive_{label}",
               *merge([box(0,-0.06,sz, 2.20,0.30,0.280),
                        box(-0.96,-0.06,sz, 0.22,0.36,0.280),
                        box( 0.96,-0.06,sz, 0.22,0.36,0.280)]), RUBBER)
        # Road wheels
        for wx in np.linspace(-0.80,0.80,5):
            b.part(f"Road_Wheel_{label}_{wx:.2f}",
                   *cyl(wx,-0.06,sz, 0.10,0.25,seg=18,axis='z'), RUBBER)
        b.part(f"Drive_Sprocket_{label}",*cyl( 0.96,-0.06,sz, 0.12,0.26,seg=18,axis='z'), STEEL)
        b.part(f"Idler_{label}",         *cyl(-0.96,-0.06,sz, 0.10,0.26,seg=18,axis='z'), STEEL)
        b.part(f"Track_Tensioner_{label}",*cyl(-1.06,0.04,sz, 0.022,0.30, axis='z'), STEEL)

    b.part("Battery_Bay",        *box(-0.45,0.26,0, 0.80,0.26,0.84), DARK)
    b.part("Battery_Cover",      *box(-0.45,0.40,0, 0.82,0.014,0.86), ALU)
    b.part("Charge_Port",        *box(-0.86,0.30,0, 0.020,0.040,0.060), DARK)
    b.part("Cargo_Flatbed",      *box(0.36,0.28,0, 1.10,0.040,0.90), ALU)
    b.part("Flatbed_Tie_Rails",  *merge([cyl(0.36,0.304,x, 0.008,1.06, axis='z')
                                          for x in [-0.44,0.44]]), STEEL)
    b.part("Sensor_Mast",        *cyl(0.82,0.60,0, 0.040,0.66), DARK)
    b.part("LiDAR_Puck",         *cyl(0.82,0.94,0, 0.062,0.062), DARK)
    b.part("LiDAR_Spinner",      *cyl(0.82,0.966,0, 0.050,0.018), ALU)
    b.part("Stereo_Camera_Pod",  *box(-0.90,0.46,0, 0.100,0.100,0.200), DARK)
    b.part("Camera_Lenses",      *merge([cyl(-0.90,0.46,x, 0.022,0.024, axis='z')
                                          for x in [-0.050,0.050]]), PC)
    b.part("Ultrasonic_Sensors", *merge([box(-1.04,0.18,x, 0.020,0.022,0.030)
                                          for x in [-0.30,0,0.30]]), DARK)
    b.part("Tow_Hitch",          *merge([box(-1.10,-0.02,0, 0.080,0.060,0.060),
                                          cyl(-1.20,-0.02,0, 0.030,0.085, axis='x')]), STEEL)
    b.save(f"{OUT}/agrimule.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  13  RowPlanter  — 12-Row Planter  1800×6000×1400 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_rowplanter():
    b=B()
    b.part("Main_Toolbar",       *box(0,0.62,0, 0.220,0.220,5.80), STEEL)
    b.part("Toolbar_Stiffeners", *merge([cyl(0,0.62,z, 0.060,0.22, axis='z')
                                          for z in np.linspace(-2.70,2.70,7)]), STEEL)
    b.part("Seed_Hopper",        *box(0,1.05,0, 0.82,0.70,3.20), HDPE)
    b.part("Hopper_Lid",         *box(0,1.42,0, 0.84,0.038,3.22), STEEL)
    b.part("Hopper_Fill_Points", *merge([cyl(0,1.46,z, 0.040,0.050)
                                          for z in np.linspace(-1.40,1.40,4)]), ALU)
    b.part("Air_Hose_Routing",   *cyl(0.12,0.62,0, 0.018,5.60, axis='z'), HDPE)
    b.part("Folding_Hinge_L",    *cyl(0,0.62,-2.72, 0.040,0.240, axis='z'), ORANGE)
    b.part("Folding_Hinge_R",    *cyl(0,0.62, 2.72, 0.040,0.240, axis='z'), ORANGE)
    b.part("3pt_Hitch_Frame",    *box(0,0.50,-0.10, 0.200,0.800,0.200), STEEL)
    b.part("Top_Link_Pin",       *cyl(0,1.05,0, 0.020,0.220, axis='z'), ALU)

    row_positions=np.linspace(-2.55,2.55,12)
    # Row units — each with proper sub-parts
    b.part("Row_Unit_Assembly",  *merge([box(0.30,0.22,z, 0.210,0.380,0.160)
                                          for z in row_positions]), STEEL)
    b.part("Pneumatic_Seed_Meters",*merge([box(0.30,0.44,z, 0.130,0.140,0.120)
                                            for z in row_positions]), DARK)
    b.part("Electric_Seed_Meter_Motor",*merge([box(0.20,0.44,z, 0.060,0.080,0.080)
                                                for z in row_positions]), DARK)
    b.part("Hydraulic_Downforce_Cylinders",
                                 *merge([cyl(0.18,0.38,z, 0.022,0.260)
                                          for z in row_positions]), STEEL)
    b.part("Closing_Wheels",     *merge([cyl(0.38,-0.030,z, 0.072,0.048, axis='z')
                                          for z in row_positions]), RUBBER)
    b.part("Closing_Wheel_Tensioner",*merge([box(0.34,0.04,z, 0.030,0.140,0.030)
                                              for z in row_positions[::2]]), STEEL)
    b.part("Depth_Gauge_Wheels", *merge([cyl(0.28,-0.015,z, 0.055,0.040, axis='z')
                                          for z in row_positions]), RUBBER)
    b.part("Opener_Disc_Blades", *merge([cyl(0.18,-0.020,z, 0.090,0.030, axis='z')
                                          for z in row_positions]), STEEL)
    b.save(f"{OUT}/rowplanter.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  14  TerraPlanter  — Tree Planter  3500×1800×2200 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_terraplanter():
    b=B()
    b.part("Tracked_Chassis",    *box(0,0.22,0, 2.90,0.54,1.56), STEEL)
    # Tracks
    for side,sz in [(-1,-0.96),(1,0.96)]:
        label='L' if side<0 else 'R'
        b.part(f"Track_{label}",
               *merge([box(0,-0.06,sz, 3.30,0.32,0.32),
                        box(-1.44,-0.06,sz, 0.22,0.40,0.32),
                        box( 1.44,-0.06,sz, 0.22,0.40,0.32)]), RUBBER)
        for wx in np.linspace(-1.20,1.20,6):
            b.part(f"Roadwheel_{label}_{wx:.1f}",*cyl(wx,-0.06,sz, 0.11,0.30,seg=18,axis='z'), RUBBER)
    b.part("Diesel_Generator",   *box(-0.90,0.72,0, 1.00,0.84,1.28), DARK)
    b.part("Generator_Hood",     *box(-0.90,1.16,0, 1.02,0.038,1.30), STEEL)
    b.part("Exhaust_Pipe",       *cyl(-0.48,1.44,0.40, 0.055,0.38), STEEL)
    b.part("Exhaust_Cap",        *dome(-0.48,1.63,0.40, 0.058,seg=12), STEEL)
    b.part("Hydraulic_Pump_Bank",*merge([box(-0.76,0.32,x, 0.180,0.260,0.180)
                                          for x in [-0.50,0.50]]), DARK)
    b.part("Hydraulic_Lines",    *merge([cyl(x,0.36,0, 0.012,0.80, axis='z')
                                          for x in [-0.66,0.66]]), RUBBER)
    # Auger boom arm
    b.part("Hydraulic_Auger_Boom",*merge([box(0.52,0.88,0, 0.100,0.100,1.50),
                                            box(1.14,0.54,0, 0.100,0.680,0.100)]), STEEL)
    b.part("Boom_Hydraulic_Cyl", *cyl(0.90,0.66,0.52, 0.040,0.600, axis='z'), STEEL)
    b.part("Hydraulic_Auger_Head",*cyl(1.14,-0.02,0, 0.130,0.320), STEEL)
    b.part("Auger_Drill_Bit",    *merge([cyl(1.14,-0.30,0, 0.060,0.380),
                                          rbox(1.14,-0.30,0, 0.055,0.500,0.005,ay=0.4)]), STEEL)
    # Robotic planting arm (5-axis)
    b.part("Robotic_Planting_Arm",*merge([
        cyl(0.40,0.70,0.66, 0.042,0.620),      # upper arm
        box(0.60,1.00,0.66, 0.420,0.076,0.076), # horizontal link
        cyl(0.82,0.74,0.66, 0.036,0.540),       # forearm
        box(0.86,0.48,0.66, 0.076,0.076,0.076), # elbow joint
    ]), GREEN)
    b.part("Sapling_Gripper",    *merge([box(0.90,0.46,0.63, 0.040,0.080,0.100),
                                          box(0.90,0.46,0.70, 0.040,0.080,0.100),
                                          cyl(0.90,0.52,0.665, 0.012,0.040, axis='z')]), ALU)
    b.part("Sapling_Magazine",   *cyl(0.12,0.78,0.66, 0.210,0.780,seg=20), HDPE)
    b.part("Rotary_Magazine_Drive",*cyl(0.12,1.17,0.66, 0.230,0.042,seg=20), STEEL)
    b.part("Sensor_Head_LiDAR",  *cyl(0.28,1.00,0, 0.060,0.060), DARK)

    b.save(f"{OUT}/terraplanter.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  15  MicroWeeder  — Laser Weeding Robot  1200×1600×800 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_microweeder():
    b=B()
    # High-clearance portal frame — aluminium extrusions
    b.part("Portal_Frame",       *merge([
        cyl(-0.76,0.08,0, 0.048,0.900),      # left upright
        cyl( 0.76,0.08,0, 0.048,0.900),      # right upright
        cyl(0,0.54,0, 0.040,1.56, axis='x'),       # top crossbar
        cyl(0,0.54,0, 0.030,1.56, axis='z'),       # front crossbar
    ]), ALU)
    b.part("Frame_Corner_Joints",*merge([box(x,0.54,z, 0.080,0.080,0.080)
                                          for x,z in [(-0.76,0),(0.76,0),
                                                       (-0.76,0.80),(0.76,0.80)]]), ALU)
    # 4 wheel-drive units at corners
    for wx,wz in [(-0.76,-0.70),( 0.76,-0.70),(-0.76,0.70),(0.76,0.70)]:
        label=f"{wx:.0f}_{wz:.0f}"
        b.part(f"Wheel_Motor_{label}",*merge([
            cyl(wx,-0.34,wz, 0.195,0.140,seg=20,axis='z'),   # wheel
            box(wx,-0.10,wz, 0.130,0.360,0.130),          # motor housing
        ]), RUBBER)
        b.part(f"Wheel_Hub_{label}",  *cyl(wx,-0.34,wz, 0.080,0.150,seg=16,axis='z'), ALU)

    # Solar canopy
    b.part("Solar_Canopy",       *solar_panel(0,0.700,0.42, 1.50,0.90, rows=4,cols=6), SOLAR)
    b.part("Solar_Grid_Lines",   *solar_panel(0,0.706,0.42, 1.46,0.86, rows=4,cols=6), SOLAR2)
    b.part("Canopy_Frame",       *merge([cyl(0,0.695,0.42, 0.016,1.50, axis='x'),
                                          cyl(0,0.695,0.42, 0.016,0.92, axis='z')]), ALU)

    # Vision core
    b.part("Vision_Core",        *box(0,0.38,0, 0.320,0.220,0.320), DARK)
    b.part("High-Speed_Camera_L",*merge([box(-0.10,0.32,-0.18, 0.065,0.065,0.042),
                                          cyl(-0.10,0.32,-0.20, 0.018,0.025, axis='z')]), DARK)
    b.part("High-Speed_Camera_R",*merge([box( 0.10,0.32,-0.18, 0.065,0.065,0.042),
                                          cyl( 0.10,0.32,-0.20, 0.018,0.025, axis='z')]), DARK)
    b.part("Camera_Lens_L",      *cyl(-0.10,0.32,-0.204, 0.014,0.022, axis='z'), PC)
    b.part("Camera_Lens_R",      *cyl( 0.10,0.32,-0.204, 0.014,0.022, axis='z'), PC)

    # Delta robot arm array (3 arms in delta triangle)
    for ang,label in [(90,'A'),(210,'B'),(330,'C')]:
        a=np.radians(ang)
        ax=np.cos(a)*0.130; az=np.sin(a)*0.130
        b.part(f"Delta_Arm_{label}_Upper",
               *rcyl(ax/2,0.28,az/2, 0.016,0.280,ay=-a), CARBON)
        b.part(f"Delta_Arm_{label}_Lower",
               *rcyl(ax*0.85,0.12,az*0.85, 0.014,0.220,ay=-a), CARBON)
        b.part(f"Delta_Joint_{label}",
               *sphere(ax,0.20,az, 0.022,seg=14), ALU)
    b.part("Delta_Arm_Pivot",    *cyl(0,0.24,0, 0.045,0.044), ALU)
    b.part("Delta_End_Plate",    *box(0,0.06,0, 0.100,0.018,0.100), ALU)

    # Laser emitter pods (3 × 50W fibre laser)
    for ang in [90,210,330]:
        a=np.radians(ang)
        lx=np.cos(a)*0.065; lz=np.sin(a)*0.065
        b.part(f"50W_Fiber_Laser_Emitter_{ang}",
               *cyl(lx,-0.010,lz, 0.024,0.060), RED)
        b.part(f"Laser_Safety_Shroud_{ang}",
               *cyl(lx,-0.018,lz, 0.030,0.042), DARK)
    b.part("50W_Fiber_Laser_Module",*box(0,0.42,0.12, 0.140,0.100,0.075), RED)
    b.save(f"{OUT}/microweeder.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  16  BrushCrusher  — Forestry Mulcher  3800×2100×1800 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_brushcrusher():
    b=B()
    b.part("Main_Chassis",       *box(0,0.46,0, 2.50,0.82,1.56), STEEL)
    # Tracks
    for side,sz in [(-1,-1.04),(1,1.04)]:
        label='L' if side<0 else 'R'
        b.part(f"Track_{label}",
               *merge([box(0,-0.04,sz, 3.60,0.42,0.38),
                        box(-1.72,-0.04,sz, 0.28,0.52,0.38),
                        box( 1.72,-0.04,sz, 0.28,0.52,0.38)]), RUBBER)
        for wx in np.linspace(-1.50,1.50,7):
            b.part(f"Road_Wheel_{label}_{wx:.1f}",*cyl(wx,-0.04,sz, 0.14,0.36,seg=20,axis='z'), RUBBER)
        b.part(f"Drive_Sprocket_{label}",*cyl( 1.72,-0.04,sz, 0.17,0.37,seg=20,axis='z'), STEEL)
        b.part(f"Idler_{label}",         *cyl(-1.72,-0.04,sz, 0.14,0.37,seg=20,axis='z'), STEEL)

    b.part("Diesel_Engine_Bay",  *box(-0.80,0.72,0, 1.70,0.86,1.50), DARK)
    b.part("Engine_Hood",        *box(-0.80,1.16,0, 1.72,0.038,1.52), STEEL)
    b.part("Engine_Hood_Louvres",*merge([box(-0.38+j*0.080,1.168,0, 0.048,0.022,1.48)
                                          for j in range(6)]), DARK)
    b.part("Exhaust_Stack",      *merge([cyl(-0.30,1.44,0.48, 0.068,0.540),
                                          dome(-0.30,1.71,0.48, 0.072,seg=16)]), STEEL)
    b.part("Air_Filter",         *cyl(-0.60,1.26,0.52, 0.088,0.240), DARK)
    b.part("Fuel_Tank",          *box(0.40,0.60,-0.50, 0.280,0.480,0.420), STEEL)
    b.part("Hydraulic_Pump_Bank",*merge([box(-0.62,0.30,z, 0.220,0.300,0.200)
                                          for z in [-0.60,0.60]]), DARK)
    b.part("Hydraulic_Lines",    *merge([cyl(0,0.44,z, 0.018,2.40, axis='x')
                                          for z in [-0.30,0,0.30]]), RUBBER)
    # Front drum mulcher — the most prominent feature
    b.part("Front_Drum_Mulcher", *cyl(1.60,0.12,0, 0.290,2.00,seg=28,axis='z'), STEEL)
    b.part("Drum_End_Cap_L",     *box(1.60,0.12,-1.02, 0.040,0.580,0.040), ALU)
    b.part("Drum_End_Cap_R",     *box(1.60,0.12, 1.02, 0.040,0.580,0.040), ALU)
    # Tungsten carbide teeth — 4 rows of teeth
    for row,ra in enumerate(np.linspace(-0.90,0.90,12)):
        b.part(f"Tungsten_Carbide_Tooth_{row}",
               *box(1.60+0.295*np.cos(row*1.0),
                    0.12+0.295*np.sin(row*1.0),
                    ra, 0.060,0.060,0.040), YELLOW)
    b.part("Hydraulic_Motor_Cover",*box(1.60,0.12,1.02, 0.220,0.320,0.080), DARK)
    b.part("Steel_Deflector_Shield",*merge([
        rbox(1.12,0.58,0, 0.840,0.042,2.04),
        box(1.12,0.58,-1.02, 0.840,0.042,0.042),
        box(1.12,0.58, 1.02, 0.840,0.042,0.042),
    ]), STEEL)
    # Sensor mast + LiDAR
    b.part("Sensor_Mast",        *cyl(-1.10,1.22,0, 0.040,0.360), DARK)
    b.part("LiDAR_Puck",         *cyl(-1.10,1.42,0, 0.062,0.060), DARK)
    b.part("Thermal_Camera",     *box(-1.10,1.10,0.46, 0.060,0.060,0.050), DARK)

    b.save(f"{OUT}/brushcrusher.glb")

# ═══════════════════════════════════════════════════════════════════════════════
#  17  OmniHarvester  — Robotic Harvester  4500×2500×3000 mm
# ═══════════════════════════════════════════════════════════════════════════════
def build_omniharvester():
    b=B()
    # Portal chassis — 4 uprights + top beams + base skids
    upright_pos=[(-1.14,-1.30),(1.14,-1.30),(-1.14,1.30),(1.14,1.30)]
    b.part("Portal_Chassis",     *merge(
        [cyl(px,1.26,pz, 0.100,2.64) for px,pz in upright_pos] +
        [box(0,2.56,pz, 2.40,0.160,0.160) for pz in [-1.30,1.30]] +
        [box(0,2.56,0, 0.160,0.160,2.64)] +          # top center beam
        [box(0,-0.02,pz, 2.40,0.080,0.080) for pz in [-1.30,1.30]] +
        [box(0,-0.02,0, 0.080,0.080,2.64)]             # base skid
    ), STEEL)
    b.part("Chassis_Gussets",    *merge([box(px,2.40,pz, 0.200,0.200,0.200)
                                          for px,pz in upright_pos]), STEEL)
    # Drive modules — 4 powered wheel/leg assemblies
    for px,pz in upright_pos:
        label=f"{'L' if px<0 else 'R'}_{'F' if pz<0 else 'R'}"
        b.part(f"Drive_Module_{label}",
               *merge([cyl(px,-0.38,pz, 0.240,0.320,seg=22,axis='z'),
                        box(px,-0.10,pz, 0.300,0.220,0.380)]), RUBBER)
        b.part(f"Wheel_Hub_{label}",*cyl(px,-0.38,pz, 0.100,0.330,seg=18,axis='z'), ALU)

    # 6 robotic harvesting arms (3 per side)
    for side,sx in [(-1,-1.14),(1,1.14)]:
        label='L' if side<0 else 'R'
        for k,yarm in enumerate([1.60,1.00,0.40]):
            b.part(f"Robotic_Arm_{label}_{k+1}",
                   *merge([
                       cyl(sx,yarm,0, 0.036,0.800,seg=24,axis='z'),   # upper arm
                       cyl(sx+(side*0.40),yarm-0.08,0, 0.030,0.560),  # forearm
                       sphere(sx+(side*0.40),yarm-0.38,0, 0.040),     # elbow joint
                       cyl(sx+(side*0.40),yarm-0.65,0, 0.026,0.520),  # wrist
                   ]), GREEN)
            # End effector (soft gripper)
            ex=sx+(side*0.40); ey=yarm-0.92
            b.part(f"Soft-Grip_End_Effector_{label}_{k+1}",
                   *merge([dome(ex,ey,0, 0.062,seg=14),
                            cyl(ex+side*0.060,ey-0.040,0, 0.016,0.070),
                            cyl(ex-side*0.060,ey-0.040,0, 0.016,0.070),
                            cyl(ex,ey-0.040,0.040, 0.016,0.070),
                            cyl(ex,ey-0.040,-0.040, 0.016,0.070)]), HDPE)
            b.part(f"Tactile_Sensor_{label}_{k+1}",
                   *dome(ex,ey+0.062,0, 0.028,seg=12), PC)
    # Stereo vision cameras (6 cameras, 2 per side × top)
    b.part("Stereo_Vision_Camera_Array",
           *merge([merge([box(px,2.46,pz, 0.130,0.090,0.090),
                           cyl(px,2.46,pz+(0.050 if pz<0 else -0.050), 0.022,0.028, axis='z')])
                   for px in [-0.60,0,0.60]
                   for pz in [-1.20,1.20]]), DARK)
    b.part("Camera_Lenses",      *merge([cyl(px,2.46,pz+(0.052 if pz<0 else -0.052), 0.016,0.020, axis='z')
                                          for px in [-0.60,0,0.60]
                                          for pz in [-1.20,1.20]]), PC)
    # Central conveyor
    b.part("Central_Conveyor",   *box(0,0.30,0, 2.10,0.080,1.70), RUBBER)
    b.part("Conveyor_Frame",     *merge([cyl(0,0.345,z, 0.040,2.10, axis='x')
                                          for z in [-0.84,0.84]]), STEEL)
    b.part("Conveyor_Drive_Roll",*merge([cyl(px,0.30,0, 0.068,1.72,seg=18,axis='z')
                                          for px in [-1.04,1.04]]), STEEL)
    # Storage bin
    b.part("Storage_Bin",        *box(0,0.70,0, 1.70,0.660,1.60), HDPE)
    b.part("Bin_Lid",            *box(0,1.035,0, 1.72,0.040,1.62), ALU)
    b.part("Bin_Fill_Level_Window",*box(0.86,0.70,0, 0.008,0.380,0.40), PC)
    b.part("LiDAR_360",          *cyl(0,2.58,0, 0.070,0.068), DARK)

    b.save(f"{OUT}/omniharvester.glb")

# ── Run all ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Famtech AgriCore — building realistic 3D models v2\n")
    jobs=[
        (build_spray_x,      "01  Spray X"),
        (build_scout,        "02  Scout"),
        (build_nest,         "03  Nest"),
        (build_watchtower,   "04  Watchtower"),
        (build_soilnode,     "05  Soilnode"),
        (build_feedpro,      "06  Feedpro"),
        (build_herdtag,      "07  Herdtag"),
        (build_aquasense,    "08  Aquasense"),
        (build_fencegrid,    "09  Fencegrid"),
        (build_hub,          "10  Hub"),
        (build_crewlink,     "11  CrewLink"),
        (build_agrimule,     "12  AgriMule"),
        (build_rowplanter,   "13  RowPlanter"),
        (build_terraplanter, "14  TerraPlanter"),
        (build_microweeder,  "15  MicroWeeder"),
        (build_brushcrusher, "16  BrushCrusher"),
        (build_omniharvester,"17  OmniHarvester"),
    ]
    for fn,name in jobs:
        print(f"  Building {name}…", end=" ", flush=True)
        try: fn()
        except Exception as e: print(f"\n  ✗ {e}")
    print("\nDone.")
