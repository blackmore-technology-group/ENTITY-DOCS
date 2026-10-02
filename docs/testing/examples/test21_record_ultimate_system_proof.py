import hashlib, json, pathlib, subprocess, sys, time
sys.path.insert(0,r"E:\ENTITY_ACTIVE\ENTITY_TESTING_20261001\qualification_site_v343")
import cv2, numpy as np
ROOT=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_ULTIMATE_TEST_20261001")
CHILD=r"E:\ENTITY_ACTIVE\_venv_entity_v3\Scripts\python.exe"
SCRIPT=str(ROOT/"ultimate_system_proof.py")
VIDEO=ROOT/"test-21-ultimate-system-proof.webm"
TRANSCRIPT=ROOT/"test-21-ultimate-system-proof.txt"
META=ROOT/"test-21-ultimate-system-proof.metadata.json"
W,H,FPS=1600,900,4
writer=cv2.VideoWriter(str(VIDEO),cv2.VideoWriter_fourcc(*"VP80"),FPS,(W,H))
if not writer.isOpened(): raise RuntimeError("VP8 WebM writer did not open")
lines=["ENTITY v3.4.3 - TEST 21","ULTIMATE END-TO-END SYSTEM PROOF","Live execution on BTG laptop","","STARTING..."]
frames=0
def draw():
    global frames
    img=np.zeros((H,W,3),dtype=np.uint8)
    cv2.putText(img,"ENTITY / BTG  |  TEST 21",(40,45),cv2.FONT_HERSHEY_SIMPLEX,0.9,(220,220,220),2,cv2.LINE_AA)
    cv2.putText(img,"Ultimate end-to-end system proof",(40,82),cv2.FONT_HERSHEY_SIMPLEX,0.72,(190,190,190),1,cv2.LINE_AA)
    y=125
    for raw in lines[-24:]:
        text=raw[:190]
        color=(170,255,170) if "PASS" in text else ((120,190,255) if text.startswith("GATE") else (225,225,225))
        cv2.putText(img,text,(40,y),cv2.FONT_HERSHEY_SIMPLEX,0.47,color,1,cv2.LINE_AA); y+=30
    writer.write(img); frames+=1
for _ in range(FPS*2): draw()
start=time.time()
p=subprocess.Popen([CHILD,SCRIPT],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
captured=[]
assert p.stdout is not None
for line in p.stdout:
    line=line.rstrip("\r\n"); captured.append(line); print(line,flush=True)
    lines.append(line)
    for _ in range(3): draw()
code=p.wait()
lines.append(""); lines.append(f"CHILD_EXIT={code}")
lines.append("FINAL_STATUS="+("PASS" if code==0 else "FAIL"))
for _ in range(FPS*3): draw()
writer.release()
TRANSCRIPT.write_text("\n".join(captured)+f"\nCHILD_EXIT={code}\n",encoding="utf-8")
sha=hashlib.sha256(VIDEO.read_bytes()).hexdigest()
meta={"schema":"entity-test-video-metadata-v1","test":21,"child_exit":code,"frames":frames,"fps":FPS,
"width":W,"height":H,"codec":"VP80","video_bytes":VIDEO.stat().st_size,"video_sha256":sha,
"elapsed_seconds":round(time.time()-start,3),"runner":SCRIPT}
META.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print("VIDEO",VIDEO,"BYTES",VIDEO.stat().st_size,"SHA256",sha,"FRAMES",frames,flush=True)
raise SystemExit(code)
