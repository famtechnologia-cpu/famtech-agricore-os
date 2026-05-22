#!/usr/bin/env python3
"""fix_viewers.py
• Replaces giant base64 data-URI with external models/xxx.glb path
• Adds camera-controls, auto-rotate, and full interactivity attributes
• Improves environment/lighting settings for maximum realism
"""
import re, os

BASE = '/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts'

# (html_file, model_file, camera_orbit)
PRODUCTS = [
    ('01_spray_x.html',      'spray_x.glb',      '-25deg 75deg auto'),
    ('02_scout.html',        'scout.glb',        '-20deg 72deg auto'),
    ('03_nest.html',         'nest.glb',         '10deg 60deg auto'),
    ('04_watchtower.html',   'watchtower.glb',   '-15deg 78deg auto'),
    ('05_soilnode.html',     'soilnode.glb',     '-30deg 70deg auto'),
    ('06_feedpro.html',      'feedpro.glb',      '-20deg 68deg auto'),
    ('07_herdtag.html',      'herdtag.glb',      '-10deg 70deg auto'),
    ('08_aquasense.html',    'aquasense.glb',    '-25deg 65deg auto'),
    ('09_fencegrid.html',    'fencegrid.glb',    '-20deg 72deg auto'),
    ('10_hub.html',          'hub.glb',          '-35deg 68deg auto'),
    ('11_crewlink.html',     'crewlink.glb',     '-10deg 65deg auto'),
    ('12_agrimule.html',     'agrimule.glb',     '-30deg 72deg auto'),
    ('13_rowplanter.html',   'rowplanter.glb',   '-10deg 80deg auto'),
    ('14_terraplanter.html', 'terraplanter.glb', '-25deg 70deg auto'),
    ('15_microweeder.html',  'microweeder.glb',  '-30deg 70deg auto'),
    ('16_brushcrusher.html', 'brushcrusher.glb', '-20deg 68deg auto'),
    ('17_omniharvester.html','omniharvester.glb','−30deg 72deg auto'),
]

# Full model-viewer opening tag — external GLB, full interactivity
MV_ATTRS = (
    'camera-controls '
    'auto-rotate '
    'auto-rotate-delay="800" '
    'rotation-per-second="25deg" '
    'environment-image="neutral" '
    'skybox-height="2m" '
    'exposure="1.35" '
    'shadow-intensity="2.2" '
    'shadow-softness="0.75" '
    'tone-mapping="aces" '
    'interaction-prompt="auto" '
    'interaction-prompt-threshold="500" '
    'min-camera-orbit="auto 5deg 0.4m" '
    'max-camera-orbit="auto 175deg 20m" '
)

ok = 0
for (html_file, glb_file, orbit) in PRODUCTS:
    path = os.path.join(BASE, html_file)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    mv_start = html.find('<model-viewer')
    if mv_start == -1:
        print(f'  SKIP (no model-viewer): {html_file}')
        continue

    # Find the end of the opening tag '>'
    # It's tricky because the src contains '>' chars in base64 potentially? No — base64 doesn't have >.
    # But model-viewer slot buttons are inside so we find the first > after <model-viewer
    tag_end = html.find('>', mv_start)
    if tag_end == -1:
        print(f'  ERROR (no tag end): {html_file}')
        continue

    old_tag = html[mv_start:tag_end + 1]

    # Build new opening tag
    new_tag = (
        f'<model-viewer '
        f'{MV_ATTRS}'
        f'camera-orbit="{orbit}" '
        f'src="models/{glb_file}">'
    )

    html = html[:mv_start] + new_tag + html[tag_end + 1:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    ok += 1
    print(f'  ✓ [{ok:02d}/17] {html_file}  →  models/{glb_file}')

print(f'\nDone — {ok}/17 files updated.')
