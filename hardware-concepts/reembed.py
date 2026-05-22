#!/usr/bin/env python3
"""reembed.py — Re-embeds GLB files as base64 data URIs so pages work
when opened directly from the filesystem (file:// protocol).
Keeps all the new model-viewer attributes added by fix_viewers.py."""

import re, os, base64

BASE   = '/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts'
MODELS = os.path.join(BASE, 'models')

PRODUCTS = [
    ('01_spray_x.html',      'spray_x.glb'),
    ('02_scout.html',        'scout.glb'),
    ('03_nest.html',         'nest.glb'),
    ('04_watchtower.html',   'watchtower.glb'),
    ('05_soilnode.html',     'soilnode.glb'),
    ('06_feedpro.html',      'feedpro.glb'),
    ('07_herdtag.html',      'herdtag.glb'),
    ('08_aquasense.html',    'aquasense.glb'),
    ('09_fencegrid.html',    'fencegrid.glb'),
    ('10_hub.html',          'hub.glb'),
    ('11_crewlink.html',     'crewlink.glb'),
    ('12_agrimule.html',     'agrimule.glb'),
    ('13_rowplanter.html',   'rowplanter.glb'),
    ('14_terraplanter.html', 'terraplanter.glb'),
    ('15_microweeder.html',  'microweeder.glb'),
    ('16_brushcrusher.html', 'brushcrusher.glb'),
    ('17_omniharvester.html','omniharvester.glb'),
]

ok = 0
for html_file, glb_file in PRODUCTS:
    html_path = os.path.join(BASE, html_file)
    glb_path  = os.path.join(MODELS, glb_file)

    if not os.path.exists(glb_path):
        print(f'  SKIP (no GLB): {glb_file}')
        continue

    with open(glb_path, 'rb') as f:
        raw = f.read()
    b64  = base64.b64encode(raw).decode('ascii')
    data_uri = f'data:model/gltf-binary;base64,{b64}'

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace src="models/xxx.glb" with data URI
    old = f'src="models/{glb_file}"'
    new = f'src="{data_uri}"'
    if old not in html:
        # Already a data URI — replace it
        html = re.sub(r'src="data:model/gltf-binary;base64,[^"]*"',
                      f'src="{data_uri}"', html, count=1)
    else:
        html = html.replace(old, new, 1)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    kb = len(raw) // 1024
    ok += 1
    print(f'  ✓ [{ok:02d}/17] {html_file}  ({kb} KB GLB → {len(b64)//1024} KB base64)')

print(f'\nDone — {ok}/17 files re-embedded.')
