import os
import sys
import json
import requests
from datetime import datetime, timedelta

# ============================================================
# DJANGO SETUP - all in one file
# ============================================================
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        ALLOWED_HOSTS=['*'],
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.staticfiles',
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.common.CommonMiddleware',
        ],
        ROOT_URLCONF=__name__,
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.request',
                ],
                'loaders': [
                    ('django.template.loaders.locmem.Loader', {}),
                ],
            },
        }],
        STATIC_URL='/static/',
        NASA_API_KEY=os.environ.get('NASA_API_KEY', 'I5WbsB1uTaN0r52t76Djc0CHcvC66J6UP9aufKbh'),
        CACHE_FILE='/tmp/asteroid_cache.json',
    )

django.setup()

# ============================================================
# NASA API
# ============================================================
NASA_NEOWS_URL = "https://api.nasa.gov/neo/rest/v1/feed"

def fetch_asteroids():
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=7)
    params = {
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "api_key": settings.NASA_API_KEY,
    }
    response = requests.get(NASA_NEOWS_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    asteroids = []
    for date_str, neo_list in data.get("near_earth_objects", {}).items():
        for neo in neo_list:
            asteroids.append(neo)
    return asteroids

def parse_asteroid(neo):
    close_approaches = neo.get("close_approach_data", [])
    if not close_approaches:
        return None
    approach = close_approaches[0]
    miss_km = float(approach.get("miss_distance", {}).get("kilometers", 9e9))
    velocity_kms = float(approach.get("relative_velocity", {}).get("kilometers_per_second", 0))
    diam_data = neo.get("estimated_diameter", {}).get("meters", {})
    diam_min = float(diam_data.get("estimated_diameter_min", 0))
    diam_max = float(diam_data.get("estimated_diameter_max", 0))
    diam_avg = (diam_min + diam_max) / 2
    return {
        "id": neo.get("id"),
        "name": neo.get("name", "Unknown"),
        "nasa_jpl_url": neo.get("nasa_jpl_url", "#"),
        "miss_distance_km": miss_km,
        "miss_distance_lunar": float(approach.get("miss_distance", {}).get("lunar", 0)),
        "velocity_kms": velocity_kms,
        "diameter_min_m": diam_min,
        "diameter_max_m": diam_max,
        "diameter_avg_m": diam_avg,
        "is_hazardous": neo.get("is_potentially_hazardous_asteroid", False),
        "approach_date": approach.get("close_approach_date", "Unknown"),
    }

def compute_threat_score(a):
    proximity_score = (1 - (min(a["miss_distance_km"], 10_000_000) / 10_000_000)) * 50
    size_score = (min(a["diameter_avg_m"], 1000) / 1000) * 30
    hazard_bonus = 20 if a["is_hazardous"] else 0
    return round(proximity_score + size_score + hazard_bonus, 2)

def get_top5(force_refresh=False):
    cache_path = settings.CACHE_FILE
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    if not force_refresh:
        try:
            with open(cache_path) as f:
                cached = json.load(f)
            if cached.get("date") == today_str:
                return cached
        except:
            pass
    raw = fetch_asteroids()
    parsed = [parse_asteroid(n) for n in raw]
    parsed = [a for a in parsed if a]
    for a in parsed:
        a["threat_score"] = compute_threat_score(a)
    parsed.sort(key=lambda x: x["threat_score"], reverse=True)
    result = {
        "date": today_str,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "total_neos_scanned": len(parsed),
        "asteroids": parsed[:5],
    }
    with open(cache_path, "w") as f:
        json.dump(result, f, indent=2)
    return result

# ============================================================
# HTML TEMPLATE
# ============================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Boston Asteroid Watch</title>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Barlow+Condensed:wght@300;400;600;700&family=Barlow:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    :root{--navy:#0a1628;--blue:#0d3270;--mid:#1a56b0;--sky:#2e86de;--red:#c0392b;--crimson:#e63946;--white:#f8f9ff;--offwhite:#e8ecf4;--gold:#f4d03f;}
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
    body{font-family:'Barlow',sans-serif;background:var(--navy);color:var(--white);min-height:100vh;}
    #starfield{position:fixed;inset:0;z-index:0;pointer-events:none;}
    .page{position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:0 24px 80px;}
    header{text-align:center;padding:52px 0 36px;}
    .site-title{font-family:'Orbitron',monospace;font-size:clamp(1.9rem,5vw,3.2rem);font-weight:900;background:linear-gradient(135deg,var(--white) 0%,var(--sky) 50%,var(--crimson) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
    .site-subtitle{font-family:'Barlow Condensed',sans-serif;font-size:1.05rem;letter-spacing:.22em;text-transform:uppercase;opacity:.7;margin-top:10px;}
    .location-badge{display:inline-flex;align-items:center;gap:7px;background:rgba(46,134,222,.15);border:1px solid rgba(46,134,222,.4);border-radius:50px;padding:5px 16px;font-family:'Barlow Condensed',sans-serif;font-size:.85rem;letter-spacing:.12em;text-transform:uppercase;color:var(--sky);margin-top:18px;}
    .meta-bar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;background:rgba(13,50,112,.55);border:1px solid rgba(46,134,222,.25);border-radius:12px;padding:14px 22px;margin-bottom:32px;backdrop-filter:blur(10px);}
    .meta-item{font-family:'Barlow Condensed',sans-serif;font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;opacity:.75;}
    .meta-item strong{color:var(--sky);}
    .refresh-btn{font-family:'Orbitron',monospace;font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;background:linear-gradient(135deg,var(--red),var(--crimson));color:var(--white);border:none;border-radius:8px;padding:10px 22px;cursor:pointer;transition:all .2s;box-shadow:0 4px 18px rgba(198,57,43,.4);}
    .refresh-btn:hover{transform:translateY(-2px);}
    .error-box{background:rgba(198,57,43,.15);border:1px solid var(--crimson);border-radius:10px;padding:18px 22px;margin-bottom:28px;color:#ffaaaa;}
    .cards-grid{display:flex;flex-direction:column;gap:20px;}
    .asteroid-card{background:rgba(13,50,112,.4);border:1px solid rgba(46,134,222,.2);border-radius:16px;padding:24px 28px;display:grid;grid-template-columns:auto 1fr auto;gap:0 24px;align-items:start;backdrop-filter:blur(8px);transition:transform .25s,border-color .25s;animation:cardIn .5s ease both;}
    @keyframes cardIn{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}
    .asteroid-card:hover{transform:translateY(-3px);border-color:rgba(46,134,222,.5);}
    .asteroid-card.hazardous{border-color:rgba(230,57,70,.4);}
    .rank{font-family:'Orbitron',monospace;font-size:2rem;font-weight:900;color:rgba(255,255,255,.12);line-height:1;min-width:42px;padding-top:4px;}
    .rank.rank-1{color:var(--crimson);opacity:.9;}
    .rank.rank-2{color:var(--sky);opacity:.7;}
    .card-header{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;}
    .asteroid-name{font-family:'Barlow Condensed',sans-serif;font-size:1.3rem;font-weight:700;}
    .tag{font-family:'Barlow Condensed',sans-serif;font-size:.7rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;padding:3px 9px;border-radius:50px;}
    .tag-hazardous{background:rgba(230,57,70,.2);border:1px solid var(--crimson);color:var(--crimson);}
    .tag-safe{background:rgba(46,134,222,.15);border:1px solid rgba(46,134,222,.4);color:var(--sky);}
    .tag-date{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);}
    .stats-row{display:flex;flex-wrap:wrap;gap:10px 28px;margin-top:12px;}
    .stat{display:flex;flex-direction:column;gap:2px;}
    .stat-label{font-family:'Barlow Condensed',sans-serif;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;opacity:.55;}
    .stat-value{font-family:'Barlow Condensed',sans-serif;font-size:1.05rem;font-weight:600;}
    .stat-value.highlight{color:var(--sky);}
    .stat-value.danger{color:var(--crimson);}
    .threat-col{text-align:center;min-width:90px;}
    .threat-score-label{font-family:'Barlow Condensed',sans-serif;font-size:.65rem;letter-spacing:.16em;text-transform:uppercase;opacity:.5;margin-bottom:5px;}
    .threat-circle{width:78px;height:78px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Orbitron',monospace;font-size:1.15rem;font-weight:700;position:relative;margin:0 auto;}
    .threat-ring{position:absolute;inset:0;border-radius:50%;border:3px solid transparent;}
    .threat-circle.high{background:rgba(230,57,70,.15);color:var(--crimson);}
    .threat-circle.high .threat-ring{border-color:var(--crimson);box-shadow:0 0 14px rgba(230,57,70,.5);}
    .threat-circle.mid{background:rgba(244,208,63,.1);color:var(--gold);}
    .threat-circle.mid .threat-ring{border-color:var(--gold);}
    .threat-circle.low{background:rgba(46,134,222,.12);color:var(--sky);}
    .threat-circle.low .threat-ring{border-color:rgba(46,134,222,.5);}
    .jpl-link{display:inline-block;margin-top:12px;font-family:'Barlow Condensed',sans-serif;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--sky);text-decoration:none;opacity:.6;}
    .jpl-link:hover{opacity:1;}
    footer{text-align:center;margin-top:60px;font-size:.75rem;opacity:.35;font-family:'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase;}
    #toast{position:fixed;bottom:28px;right:28px;background:var(--blue);border:1px solid var(--sky);border-radius:10px;padding:12px 20px;font-family:'Barlow Condensed',sans-serif;font-size:.9rem;color:var(--white);z-index:999;transform:translateY(80px);opacity:0;transition:all .35s;pointer-events:none;}
    #toast.show{transform:translateY(0);opacity:1;}
    #toast.error{border-color:var(--crimson);background:rgba(198,57,43,.3);}
    .spin{display:inline-block;animation:spin .9s linear infinite;}
    @keyframes spin{to{transform:rotate(360deg)}}
  </style>
</head>
<body>
<canvas id="starfield" style="position:fixed;inset:0;z-index:0;pointer-events:none;width:100%;height:100%;"></canvas>
<div class="page">
  <header>
    <div style="font-size:2.8rem;margin-bottom:12px;">☄️</div>
    <h1 class="site-title">Boston Asteroid Watch</h1>
    <p class="site-subtitle">Near Earth Object Threat Monitor</p>
    <div class="location-badge">📍 Boston, MA — 42.3601°N, 71.0589°W</div>
  </header>
  <div class="meta-bar">
    <div class="meta-item">Date: <strong id="dataDate">%(date)s</strong></div>
    <div class="meta-item">Fetched: <strong id="fetchedAt">%(fetched_at)s</strong></div>
    <div class="meta-item">NEOs Scanned: <strong>%(total)s</strong></div>
    <button class="refresh-btn" id="refreshBtn" onclick="refreshData()">⟳ &nbsp;Refresh Data</button>
  </div>
  %(error_html)s
  <div class="cards-grid" id="cardsGrid">%(cards_html)s</div>
  <footer>Data from NASA NeoWs API &nbsp;·&nbsp; Threat = proximity + size + hazard &nbsp;·&nbsp; Not an official NASA product</footer>
</div>
<div id="toast"></div>
<script>
(function(){
  var c=document.getElementById('starfield'),ctx=c.getContext('2d'),stars=[];
  function resize(){c.width=window.innerWidth;c.height=window.innerHeight;}
  function init(){stars=[];for(var i=0;i<220;i++)stars.push({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*1.5,a:Math.random(),da:(Math.random()-.5)*.005});}
  function draw(){ctx.clearRect(0,0,c.width,c.height);stars.forEach(function(s){s.a=Math.max(.1,Math.min(1,s.a+s.da));if(s.a<=.1||s.a>=1)s.da*=-1;ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);ctx.fillStyle='rgba(255,255,255,'+s.a+')';ctx.fill();});requestAnimationFrame(draw);}
  window.addEventListener('resize',function(){resize();init();});resize();init();draw();
})();
function showToast(msg,isError){var t=document.getElementById('toast');t.textContent=msg;t.className='show'+(isError?' error':'');clearTimeout(t._t);t._t=setTimeout(function(){t.className='';},3200);}
function refreshData(){
  var btn=document.getElementById('refreshBtn');
  btn.innerHTML='<span class="spin">⟳</span> Fetching...';
  btn.disabled=true;
  fetch('/refresh/',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
    if(d.success){showToast('✓ Updated — reloading...');setTimeout(function(){location.reload();},900);}
    else{showToast('⚠ Error: '+d.error,true);btn.innerHTML='⟳ &nbsp;Refresh Data';btn.disabled=false;}
  }).catch(function(){showToast('⚠ Network error',true);btn.innerHTML='⟳ &nbsp;Refresh Data';btn.disabled=false;});
}
</script>
</body>
</html>"""

def render_cards(asteroids):
    if not asteroids:
        return '<div style="text-align:center;padding:60px;opacity:.5;font-family:Barlow Condensed,sans-serif;text-transform:uppercase;">No data — click Refresh Data</div>'
    cards = ""
    for i, a in enumerate(asteroids, 1):
        score = a.get("threat_score", 0)
        level = "high" if score >= 50 else ("mid" if score >= 25 else "low")
        haz_tag = '<span class="tag tag-hazardous">⚠ Hazardous</span>' if a["is_hazardous"] else '<span class="tag tag-safe">✓ Safe</span>'
        diam_class = "danger" if a["diameter_avg_m"] > 200 else ""
        cards += f"""
        <div class="asteroid-card {'hazardous' if a['is_hazardous'] else ''}">
          <div class="rank rank-{i}">{i}</div>
          <div class="card-body">
            <div class="card-header">
              <span class="asteroid-name">{a['name']}</span>
              {haz_tag}
              <span class="tag tag-date">{a['approach_date']}</span>
            </div>
            <div class="stats-row">
              <div class="stat"><span class="stat-label">Miss Distance</span><span class="stat-value highlight">{a['miss_distance_km']:,.0f} km</span></div>
              <div class="stat"><span class="stat-label">Lunar Distance</span><span class="stat-value">{a['miss_distance_lunar']:.2f} LD</span></div>
              <div class="stat"><span class="stat-label">Velocity</span><span class="stat-value">{a['velocity_kms']:.2f} km/s</span></div>
              <div class="stat"><span class="stat-label">Diameter</span><span class="stat-value {diam_class}">{a['diameter_min_m']:.0f}–{a['diameter_max_m']:.0f} m</span></div>
            </div>
            <a class="jpl-link" href="{a['nasa_jpl_url']}" target="_blank">→ View on NASA JPL ↗</a>
          </div>
          <div class="threat-col">
            <div class="threat-score-label">Threat Score</div>
            <div class="threat-circle {level}"><div class="threat-ring"></div>{score:.0f}</div>
          </div>
        </div>"""
    return cards

# ============================================================
# DJANGO VIEWS
# ============================================================
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

def index(request):
    error = None
    data = {"date": "—", "fetched_at": "—", "total_neos_scanned": "—", "asteroids": []}
    try:
        data = get_top5(force_refresh=False)
    except Exception as e:
        error = str(e)
    error_html = f'<div class="error-box">⚠️ {error}</div>' if error else ""
    html = HTML_TEMPLATE % {
        "date": data.get("date", "—"),
        "fetched_at": data.get("fetched_at", "—"),
        "total": data.get("total_neos_scanned", "—"),
        "error_html": error_html,
        "cards_html": render_cards(data.get("asteroids", [])),
    }
    return HttpResponse(html)

@csrf_exempt
def refresh(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = get_top5(force_refresh=True)
        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

# ============================================================
# URL ROUTING
# ============================================================
from django.urls import path

urlpatterns = [
    path("", index),
    path("refresh/", refresh),
]

# ============================================================
# WSGI APP
# ============================================================
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    from django.core.management import call_command
    call_command("runserver", f"0.0.0.0:{port}", "--noreload")
