import json, base64, os, sys

# alltest/ 資料夾下的 captures
BASE = os.path.dirname(os.path.abspath(__file__))
captures = os.path.join(BASE, "captures")

# 最新的 session
files = sorted([f for f in os.listdir(captures) if f.endswith('.json')])
latest = os.path.join(captures, files[-1])
print(f"讀取: {latest}")

with open(latest, encoding='utf-8') as f:
    data = json.load(f)

for i, r in enumerate(data['records']):
    b64 = r.get('screenshot_b64')
    rtype = r.get('type', 'unk')
    # 短檔名：s1_click.png, s2_region.png
    short = rtype.replace('manual_','').replace('_point','_pt')
    if b64:
        fname = os.path.join(captures, f's{i+1}_{short}.png')
        with open(fname, 'wb') as f2:
            f2.write(base64.b64decode(b64))
        print(f'saved: s{i+1} ({rtype}) -> {fname}')
    else:
        print(f's{i+1} ({rtype}) -> no screenshot')
