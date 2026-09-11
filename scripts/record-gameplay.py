#!/usr/bin/env python3
"""Record silent arcade gameplay to a 1280x720 MP4.
Requires Python Playwright (Chromium installed) and ffmpeg on PATH.
The pilot only moves and picks upgrades; game rules and stats stay intact.
"""
import argparse
import base64
from pathlib import Path
import subprocess
import tempfile
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PILOT = r"""
window.__drive = function() {
  if(mode==='up') { if(++window.__choiceFrames>45) { pick(0); window.__choiceFrames=0; } return; }
  if(mode!=='play') return;
  let target=null, best=Infinity;
  for(const d of drops) { const dist=Math.hypot(d.x-P.x,d.y-P.y); if(dist<best){best=dist;target=d;} }
  if(!target) target=nearest(P.x,P.y,1e6)||{x:AW/2,y:AH/2};
  let dx=target.x-P.x,dy=target.y-P.y, n=Math.hypot(dx,dy)||1;
  dx/=n;dy/=n;
  for(const e of ents) {
    const x=P.x-e.x,y=P.y-e.y,d=Math.hypot(x,y)||1;
    if(d<160) { const repel=3*Math.pow((160-d)/160,2);dx+=x/d*repel;dy+=y/d*repel; }
  }
  keys={arrowleft:dx<-.22,arrowright:dx>.22,arrowup:dy<-.22,arrowdown:dy>.22};
};
window.__choiceFrames=0;
"""


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seconds',type=int,default=10)
    ap.add_argument('--warmup',type=int,default=0)
    ap.add_argument('--out',default='media/gameplay-wavedash.mp4')
    args=ap.parse_args()
    output=ROOT/args.out
    output.parent.mkdir(parents=True,exist_ok=True)
    (ROOT/'.js13k-check').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        browser=pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        page=browser.new_page(viewport={'width':1280,'height':720},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.add_init_script("""
          window.__raf=requestAnimationFrame.bind(window);
          window.requestAnimationFrame=()=>0;
          let seed=13; Math.random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
        """)
        page.goto((ROOT/'src/index-80.html').as_uri())
        page.evaluate(PILOT)
        state=page.evaluate('''seconds=>{
          reset();
          for(let f=0;f<(seconds||180)*60;f++) {
            __drive(); loop((f+1)*1000/60);
            if(mode==='dead') throw Error('Pilot died during warmup at '+T+' level '+lvl);
            if(!seconds && lvl>=3 && mode==='play' && ents.length>=4) break;
          }
          return {mode,T,kills,lvl};
        }''',args.warmup)
        print('Capture starts:',state,flush=True)
        page.evaluate('''async()=>{
          window.__video=document.createElement('canvas'); __video.width=1280;__video.height=720;
          window.__ctx=__video.getContext('2d'); __ctx.imageSmoothingEnabled=false;
          const stream=__video.captureStream(30);
          window.__chunks=[];
          window.__rec=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp9',videoBitsPerSecond:8000000});
          __rec.ondataavailable=e=>{if(e.data.size)__chunks.push(e.data)};
          window.__done=new Promise(resolve=>__rec.onstop=async()=>{
            const reader=new FileReader(); reader.onload=()=>resolve(reader.result.split(',')[1]);
            reader.readAsDataURL(new Blob(__chunks,{type:'video/webm'}));
          });
          __rec.start(); last=performance.now();
          window.__frames=0;
          function frame(t){ __drive();loop(t);__ctx.drawImage(C,0,0,1280,720);__frames++;window.__frameId=__raf(frame); }
          window.__frameId=__raf(frame);
        }''')
        page.wait_for_timeout(args.seconds*1000)
        state=page.evaluate('''()=>{cancelAnimationFrame(__frameId);__rec.stop();return {mode,T,kills,lvl,frames:__frames}}''')
        raw=page.evaluate('()=>__done')
        webm=Path(tmp)/'gameplay.webm'
        webm.write_bytes(base64.b64decode(raw))
        page.screenshot(path=str(ROOT/'.js13k-check/video-end.png'))
        browser.close()
        if errors: raise RuntimeError(errors)
        if state['mode']=='dead': raise RuntimeError('Pilot died during capture; choose another warmup or pilot')
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(webm),'-t',str(args.seconds),
          '-vf','fps=30','-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p',
          '-an','-movflags','+faststart',str(output)],check=True)
        print('Capture ends:',state,flush=True)
        print(output,output.stat().st_size,'bytes',flush=True)

if __name__=='__main__': main()
