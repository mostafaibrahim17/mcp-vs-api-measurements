"""Ask each server for the newest protocol revision and record what it answers with."""
import json, subprocess, sys, os, time
def handshake(cmd, env=None, timeout=90):
    e=dict(os.environ); e.update(env or {})
    p=subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=e, text=True)
    p.stdin.write(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2026-07-28","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}})+"\n"); p.stdin.flush()
    start=time.time()
    while time.time()-start<timeout:
        line=p.stdout.readline()
        if not line: break
        try: m=json.loads(line)
        except: continue
        if m.get("id")==1:
            p.kill(); return m
    p.kill(); return None
name=sys.argv[1]; m=handshake(sys.argv[2:])
if m is None: print(f"{name:12} no answer")
elif "error" in m: print(f"{name:12} rejected initialize: {m['error'].get('message','')[:80]}")
else: print(f"{name:12} answered with protocolVersion {m['result'].get('protocolVersion')}  server {m['result'].get('serverInfo',{}).get('name')} {m['result'].get('serverInfo',{}).get('version')}")
