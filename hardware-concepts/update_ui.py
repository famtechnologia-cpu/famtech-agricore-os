#!/usr/bin/env python3
"""update_ui.py — injects scroll progress bar, prev/next nav, viewer-hint pills,
and updated footer into all 17 product HTML pages."""

import re, os

BASE = '/Users/rapid-002/Famtech Agricore /AgriCore_Hardware_Concepts'

PRODUCTS = [
    ('01_spray_x.html',      'Spray X',        'UAV-01'),
    ('02_scout.html',        'Scout',          'UAV-02'),
    ('03_nest.html',         'Nest',           'INF-01'),
    ('04_watchtower.html',   'Watchtower',     'INF-02'),
    ('05_soilnode.html',     'Soilnode',       'SNS-01'),
    ('06_feedpro.html',      'Feedpro',        'SYS-01'),
    ('07_herdtag.html',      'Herdtag',        'SNS-02'),
    ('08_aquasense.html',    'Aquasense',      'SNS-03'),
    ('09_fencegrid.html',    'Fencegrid',      'SNS-04'),
    ('10_hub.html',          'Hub',            'SYS-02'),
    ('11_crewlink.html',     'CrewLink',       'W-01'),
    ('12_agrimule.html',     'AgriMule',       'M-01'),
    ('13_rowplanter.html',   'RowPlanter',     'I-01'),
    ('14_terraplanter.html', 'TerraPlanter',   'I-02'),
    ('15_microweeder.html',  'MicroWeeder',    'R-01'),
    ('16_brushcrusher.html', 'BrushCrusher',   'R-02'),
    ('17_omniharvester.html','OmniHarvester',  'H-01'),
]

PROGRESS_DIV = '  <div id="read-progress"></div>\n'

PROGRESS_JS = """  <script>
    (function(){
      var bar = document.getElementById('read-progress');
      if (!bar) return;
      function upd() {
        var h = document.documentElement.scrollHeight - window.innerHeight;
        bar.style.width = (h > 0 ? (window.scrollY / h * 100) : 0) + '%';
      }
      window.addEventListener('scroll', upd, {passive:true});
      upd();
    })();
  </script>"""

VIEWER_HINT = """      <div class="viewer-hint">
        <span class="viewer-hint-pill"><span class="icon">⟳</span>&nbsp;Drag to rotate</span>
        <span class="viewer-hint-pill"><span class="icon">⊕</span>&nbsp;Scroll to zoom</span>
        <span class="viewer-hint-pill"><span class="icon">●</span>&nbsp;Tap dots for parts</span>
      </div>"""

def make_topnav(code, prev_info, next_info):
    prev_btn = ''
    next_btn = ''
    if prev_info:
        prev_btn = f'<a href="{prev_info[0]}" class="nav-jump-btn prev">{prev_info[1]}</a>'
    if next_info:
        next_btn = f'<a href="{next_info[0]}" class="nav-jump-btn next">{next_info[1]}</a>'
    return (
        '<nav class="topnav">\n'
        '  <a href="index.html" class="nav-back">← Catalog</a>\n'
        f'  <span class="nav-brand">Famtech Hardware System · {code}</span>\n'
        f'  <div class="nav-product-jump">{prev_btn}{next_btn}</div>\n'
        '</nav>'
    )

def make_footer(prev_info, next_info):
    prev_link = ''
    next_link = ''
    if prev_info:
        prev_link = f'\n      <a href="{prev_info[0]}" class="prev">{prev_info[1]}</a>'
    if next_info:
        next_link = f'\n      <a href="{next_info[0]}" class="next">{next_info[1]}</a>'
    return (
        '<footer class="site-footer">\n'
        '    <span class="footer-brand">Famtech Industrial Design System &copy; 2026 &mdash; Internal Confidential</span>\n'
        f'    <nav class="product-footer-nav">{prev_link}{next_link}\n    </nav>\n'
        '  </footer>'
    )

changed = 0
for idx, (fname, short_name, code) in enumerate(PRODUCTS):
    path = os.path.join(BASE, fname)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    prev_info = (PRODUCTS[idx-1][0], PRODUCTS[idx-1][1]) if idx > 0 else None
    next_info = (PRODUCTS[idx+1][0], PRODUCTS[idx+1][1]) if idx < len(PRODUCTS)-1 else None

    # ── 1. Progress bar div after <body> ─────────────────────────
    if 'id="read-progress"' not in html:
        html = html.replace('<body>\n', '<body>\n' + PROGRESS_DIV, 1)

    # ── 2. Replace topnav ─────────────────────────────────────────
    new_nav = make_topnav(code, prev_info, next_info)
    html = re.sub(r'<nav class="topnav">.*?</nav>', new_nav,
                  html, count=1, flags=re.DOTALL)

    # ── 3. Viewer-hint pills inside .viewer-panel ─────────────────
    if 'viewer-hint' not in html:
        mv_end = html.find('</model-viewer>')
        if mv_end != -1:
            insert_at = mv_end + len('</model-viewer>')
            next_div  = html.find('</div>', insert_at)
            if next_div != -1:
                html = html[:next_div] + '\n' + VIEWER_HINT + '\n' + html[next_div:]

    # ── 4. Replace footer ─────────────────────────────────────────
    new_footer = make_footer(prev_info, next_info)
    html = re.sub(r'<footer[^>]*>.*?</footer>', new_footer,
                  html, count=1, flags=re.DOTALL)

    # ── 5. Progress JS before </body> ────────────────────────────
    if "upd()" not in html:
        html = html.replace('</body>', PROGRESS_JS + '\n</body>', 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    changed += 1
    print(f'  ✓ [{idx+1:02d}/17] {fname}')

print(f'\nDone — {changed}/17 files updated.')
