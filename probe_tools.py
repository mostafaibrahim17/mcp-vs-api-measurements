import json, subprocess, sys, time, os
def probe(cmd, env=None, timeout=90):
    e=dict(os.environ); e.update(env or {})
    p=subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=e, text=True)
    msgs=[{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}},
          {"jsonrpc":"2.0","method":"notifications/initialized"},
          {"jsonrpc":"2.0","id":2,"method":"tools/list"}]
    p.stdin.write(json.dumps(msgs[0])+"\n"); p.stdin.flush()
    start=time.time(); tools=None; init=None
    while time.time()-start<timeout:
        line=p.stdout.readline()
        if not line: break
        try: m=json.loads(line)
        except: continue
        if m.get("id")==1:
            init=m
            p.stdin.write(json.dumps(msgs[1])+"\n"); p.stdin.write(json.dumps(msgs[2])+"\n"); p.stdin.flush()
        elif m.get("id")==2:
            tools=m["result"]["tools"]; break
    p.kill()
    return init, tools
if __name__=="__main__":
    name=sys.argv[1]; cmd=sys.argv[2:]
    init,tools=probe(cmd)
    if tools is None: print(name,"FAILED"); sys.exit(1)
    json.dump(tools, open(f"tools_{name}.json","w"), indent=1)
    print(name, "tools:", len(tools), "server:", (init or {}).get("result",{}).get("serverInfo"))
