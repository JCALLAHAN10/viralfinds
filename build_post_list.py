import re
q = open("PIN_QUEUE.md").read()
pins = re.findall(r"## (.+?)\n- Board: (.+?)\n- Save URL: (\S+)", q)
lines = ["# POST TODAY — ViralFinds beauty pins (you click these)","",
"**How to post:** click a link -> Pinterest opens pre-filled -> pick the",
"**Beauty & Skincare Finds** board -> Publish.","",
"**Pace:** ~2/day while the account is young, at varied times. If Pinterest ever",
"shows a verify/unusual-activity screen: STOP and tell me.","","---",""]
for i,(title,board,url) in enumerate(pins,1):
    short = title.split(" (")[0][:45]
    hook = "("+title.split("(")[1] if "(" in title else ""
    lines += [f"{i}. [ ] **{short}** {hook}", f"   -> {url}", ""]
open("POST_TODAY.md","w").write("\n".join(lines))
print(f"POST_TODAY.md refreshed: {len(pins)} pins")
