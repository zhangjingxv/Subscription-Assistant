#!/usr/bin/env python3
# AttentionSync - The Ultimate Version
# "Good taste: removing code until it breaks, then adding back one line"

import sqlite3, json, time
from http.server import *
from urllib.request import urlopen
from xml.etree.ElementTree import fromstring

db = sqlite3.connect(':memory:', check_same_thread=False)
db.execute('CREATE TABLE i(h TEXT UNIQUE,t TEXT,u TEXT,c TEXT,d INT)')

class H(BaseHTTPRequestHandler):
    def do_GET(s):
        p = s.path.split('?')[0]
        if p == '/':
            s.send_response(200)
            s.end_headers()
            s.wfile.write(b'''<html><style>*{margin:0;font-family:system-ui}body{max-width:600px;margin:50px auto;padding:20px}h1{margin:20px 0}input,button{padding:10px;margin:10px 0}div{border-left:3px solid #07f;padding:10px;margin:15px 0}a{color:#07f}</style><h1>AttentionSync</h1><input id=u placeholder="RSS URL"><button onclick="location='/add?u='+u.value">Add</button><div id=d></div><script>fetch('/d').then(r=>r.json()).then(i=>d.innerHTML=i.map(x=>`<div><b>${x.t}</b><br>${x.c}<br><a href="${x.u}">→</a></div>`).join('')||'No items')</script></html>''')
        elif p == '/add':
            u = s.path.split('u=')[1] if 'u=' in s.path else ''
            if u:
                try:
                    for i in fromstring(urlopen(u).read()).findall('.//item')[:10]:
                        try: db.execute('INSERT INTO i VALUES(?,?,?,?,?)',(hash(i.findtext('link')),i.findtext('title')[:99],i.findtext('link'),i.findtext('description')[:199],int(time.time())))
                        except: pass
                    db.commit()
                except: pass
            s.send_response(302)
            s.send_header('Location','/')
            s.end_headers()
        elif p == '/d':
            s.send_response(200)
            s.end_headers()
            s.wfile.write(json.dumps([{'t':r[0],'u':r[1],'c':r[2]} for r in db.execute('SELECT t,u,c FROM i WHERE d>? ORDER BY d DESC LIMIT 10',(int(time.time())-86400,))]).encode())
    def log_message(s,*a):0

print('→ http://localhost:8000')
HTTPServer(('',8000),H).serve_forever()