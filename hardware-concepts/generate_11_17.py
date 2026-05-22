import os

template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NAME} - Specification</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;700&family=Outfit:wght@600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
  <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.1.1/model-viewer.min.js"></script>
</head>
<body>
  <div class="container">
    <a href="index.html" class="nav-back">Back to Hardware System</a>
    
    <header>
      <span class="badge" style="margin-bottom: 1rem;">{BADGE}</span>
      <h1>{NAME}</h1>
      <p>{ROLE}</p>
    </header>

    <section>
      <h2>Product Concept Renders</h2>
      <div class="grid grid-2">
        <div class="panel">
          <div class="img-placeholder">
            [ 2D Render Processing ]<br>API Rate Limit Active
          </div>
          <p style="font-family: var(--font-mono); font-size: 0.85rem; text-align: center;">Hero Render Perspective</p>
        </div>
      </div>
    </section>

    <section>
      <h2>360° Interactive View</h2>
      <div class="panel" style="height: 400px; padding: 0; overflow: hidden; position: relative;">
        <model-viewer src="models/{FILE_ID}.glb" 
                      alt="3D model of {FILE_ID}" 
                      auto-rotate 
                      camera-controls 
                      shadow-intensity="1"
                      style="width: 100%; height: 100%; background-color: var(--panel-bg);">
          <div slot="poster" style="display:flex; align-items:center; justify-content:center; height:100%; color:var(--accent-color); font-family:var(--font-mono);">
            [ Drop {FILE_ID}.glb in models/ folder to view ]
          </div>
        </model-viewer>
      </div>
    </section>

    <section>
      <h2>1. Industrial Design Brief</h2>
      <div class="panel">
        <p><strong>Product Name:</strong> {NAME}</p>
        <p><strong>AgriCore Role:</strong> {ROLE}</p>
        <p><strong>Target User:</strong> {USER}</p>
        <p><strong>Deployment Environment:</strong> {ENV}</p>
        <p><strong>Product Category:</strong> {CAT}</p>
        <p><strong>Mounting / Form Factor:</strong> {FORM}</p>
        <h4 style="margin-top:1rem; color: #fff;">Visual Priorities</h4>
        <p>{VISUAL}</p>
      </div>
    </section>

    <section>
      <h2>2. Product Specification Sheet</h2>
      <div class="panel">
        <table class="spec-table">
          <tr><th>Power System</th><td>{POW}</td></tr>
          <tr><th>Battery Specs</th><td>{BAT}</td></tr>
          <tr><th>Runtime</th><td>{RUN}</td></tr>
          <tr><th>Charging Method</th><td>{CHG}</td></tr>
          <tr><th>Connectivity</th><td>{CON}</td></tr>
          <tr><th>Sensor Suite</th><td>{SEN}</td></tr>
          <tr><th>Processing Hardware</th><td>{COM}</td></tr>
          <tr><th>Ingress Protection</th><td>{IP}</td></tr>
          <tr><th>Operating Temp</th><td>{TMP}</td></tr>
        </table>
      </div>
    </section>

    <section>
      <h2>3. Dimension Proposal</h2>
      <div class="panel">
        <table class="spec-table">
          <tr><th>Overall Length</th><td>{L}</td></tr>
          <tr><th>Overall Width</th><td>{W}</td></tr>
          <tr><th>Overall Height</th><td>{H}</td></tr>
          <tr><th>Ground Clearance</th><td>{GC}</td></tr>
          <tr><th>Weight Targets</th><td>Empty: {EW} | Operating: {OW} | MTOW: {MTOW}</td></tr>
          <tr><th>Payload/Tank Volume</th><td>{VOL}</td></tr>
        </table>
      </div>
    </section>

    <section>
      <h2>4. Orthographic Dimensions</h2>
      <div class="panel">
        <table class="spec-table">
          <tr><th>Working Width/Span</th><td>{SPAN}</td></tr>
          <tr><th>Folded Dimensions</th><td>{FOLD}</td></tr>
          <tr><th>Wheelbase / Track</th><td>{WHEEL}</td></tr>
        </table>
      </div>
    </section>

    <section>
      <h2>5. Component Map</h2>
      <div class="panel">
        <ul style="color:var(--text-muted); font-size:0.9rem; padding-left:1.2rem;">
          {COMP}
        </ul>
      </div>
    </section>

    <section>
      <h2>6. Mechanical Architecture</h2>
      <div class="panel">
        <p style="font-size:0.9rem;">{MECH}</p>
      </div>
    </section>

    <section>
      <h2>7. Materials & Finishes</h2>
      <div class="panel">
        <p style="font-size:0.9rem;">{MAT}</p>
      </div>
    </section>

    <section>
      <h2>8. Fusion Build Sequence</h2>
      <div class="panel">
        <ol style="color:var(--text-color); font-family:var(--font-mono); font-size:0.85rem; padding-left:1.5rem;">
          {FUS}
        </ol>
      </div>
    </section>

    <section>
      <h2>9. Rendering Instructions</h2>
      <div class="panel">
        <p style="font-size:0.9rem;"><strong>Render Style:</strong> Premium industrial presentation, realistic PBR materials, dark neutral background, studio lighting.</p>
        <p style="font-size:0.9rem;"><strong>Required Views:</strong> {VIEWS}</p>
      </div>
    </section>

    <section>
      <h2>10. Annotation / Callout List</h2>
      <div class="panel">
        <ul style="color:var(--text-muted); font-size:0.9rem; padding-left:1.2rem;">
          {ANN}
        </ul>
      </div>
    </section>

    <section>
      <h2>11. Engineering Risks & Unknowns</h2>
      <div class="panel risk-alert">
        <ul style="padding-left:1.2rem; font-size:0.9rem;">
          {RSK}
        </ul>
      </div>
    </section>

    <section>
      <h2>12. Manufacturing Notes</h2>
      <div class="panel">
        <p style="font-size:0.9rem;">{MFG}</p>
      </div>
    </section>

    <section>
      <h2>13. Maintenance & Serviceability Notes</h2>
      <div class="panel">
        <p style="font-size:0.9rem;">{MNT}</p>
      </div>
    </section>

    <footer>
      AgriCore Industrial Design System &copy; 2026. Internal Confidential.
    </footer>
  </div>
</body>
</html>
"""

data = {
    "11_crewlink": {
        "FILE_ID": "crewlink", "BADGE": "W-01", "NAME": "AgriCore CrewLink", "ROLE": "Worker Tracking & Safety Wearable", "USER": "Farm Workers",
        "ENV": "Global", "CAT": "WEARABLE", "FORM": "HANDHELD / CLIP-ON", "VISUAL": "COMPACT / RUGGED / HI-VIS",
        "POW": "Battery", "BAT": "3.7V 800mAh Li-Po", "RUN": "72 Hours", "CHG": "Magnetic Wireless / Pogo Pin",
        "CON": "LoRa Mesh, BLE, RTK GPS", "SEN": "Heart Rate, Temp, Fall Detection IMU", "COM": "Nordic nRF52", "IP": "IP67", "TMP": "-20°C to 50°C",
        "L": "65 mm", "W": "45 mm", "H": "18 mm", "GC": "N/A", "EW": "0.08 kg", "OW": "0.08 kg", "MTOW": "N/A", "VOL": "N/A",
        "SPAN": "N/A", "FOLD": "N/A", "WHEEL": "N/A",
        "COMP": "<li>Polycarbonate Core</li><li>TPU Overmold Bumper</li><li>E-Ink Display</li><li>SOS Button</li><li>Biometric Sensor Window</li>",
        "MECH": "Ultrasonically welded clam shell with integrated TPU bumper. Magnetic charging pins on rear. Heavy-duty steel belt clip.",
        "MAT": "Polycarbonate, TPU rubber, Sapphire glass sensor window.",
        "FUS": "<li>Front_Housing</li><li>PCB_Core</li><li>E-Ink_Panel</li><li>Rear_Housing</li><li>Steel_Clip</li>",
        "VIEWS": "Front 3/4 Hero, Exploded Biometrics",
        "ANN": "<li>SOS Emergency Button</li><li>E-Ink Display</li><li>LoRa Antenna</li>",
        "RSK": "<li>False positives on fall detection</li><li>Screen cracking from impacts</li>",
        "MFG": "Two-shot injection molding.",
        "MNT": "Wipe clean. No user serviceable parts."
    },
    "12_agrimule": {
        "FILE_ID": "agrimule", "BADGE": "M-01", "NAME": "AgriCore AgriMule", "ROLE": "Autonomous Cargo UGV", "USER": "Farm Operations",
        "ENV": "Global", "CAT": "AUTONOMOUS VEHICLE", "FORM": "SELF-PROPELLED MACHINE", "VISUAL": "HEAVY-DUTY / INDUSTRIAL / WIDE STANCE",
        "POW": "Electric", "BAT": "48V 200Ah LiFePO4", "RUN": "10 Hours", "CHG": "Fast Charge",
        "CON": "RTK GPS, 5G, LoRa", "SEN": "3D LiDAR, Stereo Cameras, Ultrasonic", "COM": "NVIDIA Jetson AGX Orin", "IP": "IP65", "TMP": "-10°C to 50°C",
        "L": "2400 mm", "W": "1500 mm", "H": "850 mm", "GC": "350 mm", "EW": "850 kg", "OW": "1850 kg", "MTOW": "1850 kg", "VOL": "1000 kg Payload",
        "SPAN": "N/A", "FOLD": "N/A", "WHEEL": "1300 mm",
        "COMP": "<li>Steel Chassis</li><li>Tracked Drive Units</li><li>Battery Bay</li><li>Cargo Flatbed</li><li>Sensor Mast</li>",
        "MECH": "Dual independent electric drive motors coupled to rubber tracks. Low-slung steel ladder frame. Flatbed features standardized tie-downs.",
        "MAT": "High-strength low-alloy (HSLA) steel frame, aluminum diamond plate bed, reinforced rubber tracks.",
        "FUS": "<li>Ladder_Frame</li><li>Track_Drive_L</li><li>Track_Drive_R</li><li>Battery_Pack</li><li>Cargo_Bed</li>",
        "VIEWS": "Front 3/4 Hero, Undercarriage Cutaway",
        "ANN": "<li>LiDAR Puck</li><li>Track Tensioner</li><li>Tow Hitch</li>",
        "RSK": "<li>Track derailment in heavy mud</li><li>Battery degradation in extreme heat</li>",
        "MFG": "Welded steel frame, bolted assemblies, off-the-shelf track modules.",
        "MNT": "Grease track idlers every 50 hours. Battery modules slide out for replacement."
    },
    "13_rowplanter": {
        "FILE_ID": "rowplanter", "BADGE": "I-01", "NAME": "AgriCore RowPlanter", "ROLE": "Precision Row Crop Planter", "USER": "Row Crop Farmers",
        "ENV": "Global", "CAT": "IMPLEMENT", "FORM": "TRACTOR ATTACHMENT", "VISUAL": "INDUSTRIAL / MODULAR / HEAVY-DUTY",
        "POW": "PTO + Electric", "BAT": "N/A", "RUN": "Continuous", "CHG": "Tractor Alt",
        "CON": "ISOBUS, CAN BUS", "SEN": "Seed drop counters, Downforce sensors", "COM": "Industrial PLC", "IP": "IP66", "TMP": "-10°C to 50°C",
        "L": "1800 mm", "W": "6000 mm", "H": "1400 mm", "GC": "Adjustable", "EW": "1200 kg", "OW": "1800 kg", "MTOW": "N/A", "VOL": "600 L Seed Hopper",
        "SPAN": "6000 mm (12 Row)", "FOLD": "3000 x 1800 x 2200 mm", "WHEEL": "N/A",
        "COMP": "<li>Toolbar Frame</li><li>Pneumatic Seed Meters</li><li>Hydraulic Downforce Cylinders</li><li>Closing Wheels</li><li>Seed Hopper</li>",
        "MECH": "Folding steel toolbar. Individual electrically-driven seed meters with pneumatic delivery. Hydraulic active downforce on each row unit.",
        "MAT": "Welded square steel tubing, cast iron row units, HDPE hoppers.",
        "FUS": "<li>Main_Toolbar</li><li>Row_Unit_Assy</li><li>Seed_Hopper</li><li>Folding_Hinge</li>",
        "VIEWS": "Front 3/4 Field View, Row Unit Close-up",
        "ANN": "<li>Electric Seed Meter</li><li>Closing Wheel Tensioner</li><li>Air Hose Routing</li>",
        "RSK": "<li>Pneumatic tube blockages</li><li>Inconsistent depth in rocky soil</li>",
        "MFG": "Heavy steel fabrication, cast iron components for weight/durability.",
        "MNT": "Grease zerks on all pivot points. Seed disks require annual replacement."
    },
    "14_terraplanter": {
        "FILE_ID": "terraplanter", "BADGE": "I-02", "NAME": "AgriCore TerraPlanter", "ROLE": "Tree & Forestry Planter", "USER": "Orchards / Forestry",
        "ENV": "Canada / Global", "CAT": "ROBOT", "FORM": "SELF-PROPELLED MACHINE", "VISUAL": "RUGGED / HEAVY-DUTY",
        "POW": "Diesel-Electric Hybrid", "BAT": "48V Buffer Battery", "RUN": "12 Hours", "CHG": "Diesel Generator",
        "CON": "RTK GPS, 5G", "SEN": "LiDAR, Ground Penetrating Radar", "COM": "Edge AI Module", "IP": "IP65", "TMP": "-20°C to 45°C",
        "L": "3500 mm", "W": "1800 mm", "H": "2200 mm", "GC": "400 mm", "EW": "3200 kg", "OW": "4500 kg", "MTOW": "4500 kg", "VOL": "100 Saplings",
        "SPAN": "N/A", "FOLD": "N/A", "WHEEL": "1500 mm",
        "COMP": "<li>Tracked Chassis</li><li>Hydraulic Auger</li><li>Robotic Planting Arm</li><li>Sapling Magazine</li>",
        "MECH": "Heavy tracked undercarriage. A 5-axis hydraulic robotic arm picks saplings from a rotary magazine. A massive hydraulic auger drills the hole.",
        "MAT": "Armor-grade steel plating, heavy-duty hydraulic lines, aluminum magazine.",
        "FUS": "<li>Track_Base</li><li>Diesel_Gen</li><li>Auger_Boom</li><li>Planting_Arm</li><li>Sapling_Mag</li>",
        "VIEWS": "Front 3/4 Action View, Auger Mechanism Details",
        "ANN": "<li>Hydraulic Auger Head</li><li>Sapling Gripper</li><li>Rotary Magazine</li>",
        "RSK": "<li>Auger stalling on large rocks</li><li>Sapling damage by gripper</li>",
        "MFG": "Heavy plate steel welding, off-the-shelf hydraulic cylinders.",
        "MNT": "Hydraulic fluid checks every 100 hrs. Auger teeth replacement."
    },
    "15_microweeder": {
        "FILE_ID": "microweeder", "BADGE": "R-01", "NAME": "AgriCore MicroWeeder", "ROLE": "Precision Laser/Blade Weeding", "USER": "Organic Farms",
        "ENV": "Global", "CAT": "ROBOT", "FORM": "SELF-PROPELLED MACHINE", "VISUAL": "CLEAN / PRECISE / COMPACT",
        "POW": "Solar + Battery", "BAT": "24V 100Ah Li-Ion", "RUN": "14 Hours", "CHG": "Solar Roof + Mains",
        "CON": "RTK GPS, Wi-Fi", "SEN": "High-speed RGB Cameras, LiDAR", "COM": "NVIDIA Jetson Orin", "IP": "IP65", "TMP": "0°C to 45°C",
        "L": "1200 mm", "W": "1600 mm", "H": "800 mm", "GC": "600 mm", "EW": "140 kg", "OW": "140 kg", "MTOW": "N/A", "VOL": "N/A",
        "SPAN": "1600 mm", "FOLD": "N/A", "WHEEL": "1400 mm",
        "COMP": "<li>Solar Canopy</li><li>Vision Core</li><li>Delta-Robot Blade Arms</li><li>Laser Emitter Pods</li>",
        "MECH": "High-clearance portal frame. Downward-facing cameras identify weeds; high-speed delta robots slice them or 50W lasers burn the meristem.",
        "MAT": "Extruded aluminum framing, carbon fiber delta arms, polycarbonate solar canopy.",
        "FUS": "<li>Portal_Frame</li><li>Wheel_Motors</li><li>Vision_Box</li><li>Delta_Arm_Array</li>",
        "VIEWS": "Front 3/4 Hero, Underside Vision Close-up",
        "ANN": "<li>50W Fiber Laser</li><li>High-Speed Camera</li><li>Delta Arm Pivot</li>",
        "RSK": "<li>Camera obscured by dust</li><li>Laser starting fires in dry conditions</li>",
        "MFG": "Aluminum extrusion assembly, 3D printed sensor shrouds.",
        "MNT": "Lens cleaning daily. Delta arm bearing lubrication monthly."
    },
    "16_brushcrusher": {
        "FILE_ID": "brushcrusher", "BADGE": "R-02", "NAME": "AgriCore BrushCrusher", "ROLE": "Forestry Mulcher & Clearing", "USER": "Land Clearing Contractors",
        "ENV": "Canada / Global", "CAT": "ROBOT", "FORM": "SELF-PROPELLED MACHINE", "VISUAL": "BRUTALIST / HEAVY-DUTY / RUGGED",
        "POW": "Diesel-Hydraulic", "BAT": "N/A", "RUN": "10 Hours", "CHG": "Refuel",
        "CON": "Starlink, RTK GPS", "SEN": "LiDAR, Thermal, Radar", "COM": "Dual Edge AI Box", "IP": "IP66", "TMP": "-30°C to 50°C",
        "L": "3800 mm", "W": "2100 mm", "H": "1800 mm", "GC": "450 mm", "EW": "5500 kg", "OW": "6000 kg", "MTOW": "6000 kg", "VOL": "150L Diesel",
        "SPAN": "2000 mm Mulcher", "FOLD": "N/A", "WHEEL": "1800 mm",
        "COMP": "<li>Tracked Base</li><li>Diesel Engine Bay</li><li>Hydraulic Pumps</li><li>Front Drum Mulcher</li>",
        "MECH": "Massive steel tracked chassis housing a 200HP diesel engine. Direct hydraulic drive to the front-mounted high-speed forestry mulching drum.",
        "MAT": "AR400 abrasion-resistant steel, heavy forged tungsten carbide teeth.",
        "FUS": "<li>Main_Chassis</li><li>Engine_Block</li><li>Hydraulic_Routing</li><li>Mulcher_Drum</li>",
        "VIEWS": "Front 3/4 Hero, Mulcher Drum Detail",
        "ANN": "<li>Tungsten Carbide Teeth</li><li>Hydraulic Motor Cover</li><li>Steel Deflector Shield</li>",
        "RSK": "<li>Flying debris damaging sensors</li><li>Hydraulic hose ruptures</li>",
        "MFG": "Thick plate steel cutting, heavy welding, cast steel components.",
        "MNT": "Daily inspection of mulcher teeth. Hydraulic filter changes."
    },
    "17_omniharvester": {
        "FILE_ID": "omniharvester", "BADGE": "H-01", "NAME": "AgriCore OmniHarvester", "ROLE": "Autonomous Modular Harvester", "USER": "Commercial Farms",
        "ENV": "Global", "CAT": "HARVESTER", "FORM": "SELF-PROPELLED MACHINE", "VISUAL": "MODULAR / INDUSTRIAL / LARGE",
        "POW": "Electric Hybrid", "BAT": "800V Architecture", "RUN": "16 Hours", "CHG": "Fast Charge / Generator",
        "CON": "RTK GPS, 5G", "SEN": "Stereo RGB Arrays, LiDAR, Tactile Sensors", "COM": "NVIDIA Drive Platform", "IP": "IP65", "TMP": "-10°C to 45°C",
        "L": "4500 mm", "W": "2500 mm", "H": "3000 mm", "GC": "800 mm", "EW": "4200 kg", "OW": "6000 kg", "MTOW": "N/A", "VOL": "2000L Bin",
        "SPAN": "2500 mm", "FOLD": "N/A", "WHEEL": "2200 mm",
        "COMP": "<li>Portal Chassis</li><li>Robotic Harvesting Arms</li><li>Conveyor System</li><li>Storage Bin</li>",
        "MECH": "High-clearance portal frame straddles crop rows. Multiple modular 6-axis robotic arms with soft-grip end effectors pick crops and drop them onto a central conveyor.",
        "MAT": "Steel box tubing, aluminum arm linkages, silicone soft-grippers.",
        "FUS": "<li>Portal_Frame</li><li>Drive_Modules</li><li>Robotic_Arms</li><li>Conveyor_Belt</li><li>Storage_Bin</li>",
        "VIEWS": "Front 3/4 Action View, End-effector Close-up",
        "ANN": "<li>Soft-Grip End Effector</li><li>Stereo Vision Camera</li><li>Central Conveyor</li>",
        "RSK": "<li>Bruising delicate fruits</li><li>Slow picking speeds vs human labor</li>",
        "MFG": "Welded structural steel, precision CNC robotic arm joints.",
        "MNT": "Soft grippers require frequent replacement. Conveyor belt tensioning."
    }
}

for basename, specs in data.items():
    filepath = f'/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts/{basename}.html'
    with open(filepath, 'w') as f:
        f.write(template.format(**specs))
    print(f"Generated {basename}")

