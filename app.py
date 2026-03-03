import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Dino Oyunu", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
body, .stApp { background: #1a1a2e; color: #e0e0e0; }
h1, h2, h3 { font-family: "Press Start 2P", monospace !important; color: #00ff88 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# Dino Oyunu")
st.markdown("**Space / Tikla** ile zipla | Her 100 puan hiz artar!")

SCORES_FILE = "high_scores.csv"

def load_scores():
    if os.path.exists(SCORES_FILE):
        return pd.read_csv(SCORES_FILE)
    return pd.DataFrame(columns=["Isim", "Skor", "Tarih"])

def save_score(name, score):
    df = load_scores()
    new_row = pd.DataFrame([{"Isim": name, "Skor": score,
                              "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M")}])
    df = pd.concat([df, new_row], ignore_index=True)
    df = df.sort_values("Skor", ascending=False).head(10)
    df.to_csv(SCORES_FILE, index=False)
    return df

GAME_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#1a1a2e; display:flex; flex-direction:column; align-items:center;
         justify-content:center; min-height:100vh; font-family:'Press Start 2P',monospace; overflow:hidden; }
  canvas { border:2px solid #00ff88; border-radius:8px;
           box-shadow:0 0 30px #00ff8844; display:block; max-width:100%; cursor:pointer; }
  #ui { color:#00ff88; font-size:10px; margin-top:10px; text-align:center; }
</style>
</head>
<body>
<canvas id="gameCanvas"></canvas>
<div id="ui">SPACE veya TIKLA ile ZIPLA</div>
<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

function resize() {
  const maxW = Math.min(window.innerWidth - 20, 800);
  canvas.width = maxW;
  canvas.height = Math.round(maxW * 0.3);
}
resize();
window.addEventListener('resize', resize);

let gameState = 'waiting';
let score = 0, hiScore = 0, gameSpeed = 3, lastSpeedUp = 0;
let scoreTimer = 0;

const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
let audioCtx;
function initAudio() { if (!audioCtx) audioCtx = new AudioCtxClass(); }
function playBeep(freq, dur, type, vol) {
  if (!audioCtx) return;
  try {
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.connect(g); g.connect(audioCtx.destination);
    o.type = type || 'square';
    o.frequency.setValueAtTime(freq, audioCtx.currentTime);
    g.gain.setValueAtTime(vol || 0.12, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + dur);
    o.start(); o.stop(audioCtx.currentTime + dur);
  } catch(e) {}
}

const dino = {
  x:80, y:0, w:0, h:0, vy:0, grounded:true, legFrame:0, legTimer:0,
  get ground() { return canvas.height - 60; },
  reset() {
    this.w = canvas.width * 0.055;
    this.h = this.w * 1.2;
    this.y = this.ground - this.h;
    this.vy = 0; this.grounded = true;
  },
  jump() {
    if (this.grounded) {
      this.vy = -canvas.height * 0.022;
      this.grounded = false;
      playBeep(440, 0.1);
    }
  },
  update() {
    this.vy += canvas.height * 0.0012;
    this.y += this.vy;
    if (this.y >= this.ground - this.h) {
      this.y = this.ground - this.h; this.vy = 0; this.grounded = true;
    }
    if (this.grounded) {
      this.legTimer++;
      if (this.legTimer > 8) { this.legFrame = (this.legFrame+1)%2; this.legTimer=0; }
    }
  },
  draw() {
    const x=this.x, y=this.y, w=this.w, h=this.h;
    ctx.fillStyle='#00ff88';
    ctx.beginPath(); ctx.roundRect(x, y+h*0.25, w, h*0.55, 4); ctx.fill();
    ctx.beginPath(); ctx.roundRect(x+w*0.35, y, w*0.65, h*0.45, 5); ctx.fill();
    ctx.fillStyle='#1a1a2e';
    ctx.beginPath(); ctx.arc(x+w*0.88, y+h*0.12, w*0.07, 0, Math.PI*2); ctx.fill();
    ctx.fillRect(x+w*0.75, y+h*0.3, w*0.22, 3);
    ctx.fillStyle='#00cc66';
    ctx.beginPath();
    ctx.moveTo(x, y+h*0.45); ctx.lineTo(x-w*0.4, y+h*0.6); ctx.lineTo(x, y+h*0.65);
    ctx.fill();
    ctx.fillStyle='#00ff88';
    const legY=y+h*0.78, legH=h*0.22;
    if (this.grounded) {
      const off = this.legFrame===0?2:-2;
      ctx.fillRect(x+w*0.2, legY-off, w*0.18, legH+off);
      ctx.fillRect(x+w*0.55, legY+off, w*0.18, legH-off);
    } else {
      ctx.fillRect(x+w*0.2, legY-4, w*0.18, legH);
      ctx.fillRect(x+w*0.55, legY+4, w*0.18, legH-4);
    }
  }
};

let obstacles=[], nextObstacle=80;
function spawnObstacle() {
  const types=[
    {w:0.035,h:0.25,color:'#ff6b6b'},
    {w:0.025,h:0.35,color:'#ff9f43'},
    {w:0.05,h:0.2,color:'#ff6b6b'}
  ];
  const t=types[Math.floor(Math.random()*types.length)];
  const count=Math.random()<0.3?2:1;
  for (let i=0;i<count;i++) {
    const cw=canvas.width*t.w, ch=canvas.height*t.h;
    obstacles.push({x:canvas.width+20+i*(cw+6), y:dino.ground-ch, w:cw, h:ch, color:t.color});
  }
}
function drawCactus(o) {
  ctx.fillStyle=o.color;
  ctx.beginPath(); ctx.roundRect(o.x+o.w*0.35, o.y, o.w*0.3, o.h, 4); ctx.fill();
  ctx.beginPath(); ctx.roundRect(o.x, o.y+o.h*0.3, o.w*0.35, o.h*0.18, 3); ctx.fill();
  ctx.beginPath(); ctx.roundRect(o.x, o.y+o.h*0.2, o.w*0.18, o.h*0.28, 3); ctx.fill();
  ctx.beginPath(); ctx.roundRect(o.x+o.w*0.65, o.y+o.h*0.4, o.w*0.35, o.h*0.18, 3); ctx.fill();
  ctx.beginPath(); ctx.roundRect(o.x+o.w*0.82, o.y+o.h*0.3, o.w*0.18, o.h*0.28, 3); ctx.fill();
}

let clouds=[];
for(let i=0;i<5;i++) clouds.push({
  x:Math.random()*800, y:Math.random()*60+10,
  w:Math.random()*60+40, opacity:Math.random()*0.15+0.05,
  speed:Math.random()*0.5+0.3
});
function drawCloud(c) {
  ctx.fillStyle='rgba(255,255,255,'+c.opacity+')';
  ctx.beginPath(); ctx.ellipse(c.x,c.y,c.w,c.w*0.35,0,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(c.x-c.w*0.3,c.y+3,c.w*0.5,c.w*0.25,0,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(c.x+c.w*0.3,c.y+5,c.w*0.45,c.w*0.22,0,0,Math.PI*2); ctx.fill();
}

let groundOffset=0;
let groundDots=[];
for(let i=0;i<30;i++) groundDots.push({x:Math.random()*800, size:Math.random()*3+1});
function drawGround() {
  const gy=dino.ground;
  ctx.strokeStyle='#00ff8888'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(0,gy); ctx.lineTo(canvas.width,gy); ctx.stroke();
  ctx.fillStyle='#00ff8844';
  groundDots.forEach(d=>{
    let rx=(d.x-groundOffset*0.5)%canvas.width;
    if(rx<0) rx+=canvas.width;
    ctx.beginPath(); ctx.arc(rx, gy+6+d.size, d.size, 0, Math.PI*2); ctx.fill();
  });
}

function checkCollision() {
  const m=0.15;
  const dx=dino.x+dino.w*m, dw=dino.w*(1-2*m);
  const dy=dino.y+dino.h*m, dh=dino.h*(1-2*m);
  for(const o of obstacles){
    if(dx<o.x+o.w*0.9 && dx+dw>o.x+o.w*0.1 && dy<o.y+o.h && dy+dh>o.y) return true;
  }
  return false;
}

function txt(text, x, y, size, color, align) {
  ctx.font=size+'px "Press Start 2P",monospace';
  ctx.fillStyle=color; ctx.textAlign=align||'left';
  ctx.fillText(text,x,y);
}

function gameLoop() {
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle='#0d0d1a'; ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle='#ffffff05'; ctx.lineWidth=1;
  for(let i=0;i<canvas.width;i+=40){ctx.beginPath();ctx.moveTo(i,0);ctx.lineTo(i,canvas.height);ctx.stroke();}
  for(let i=0;i<canvas.height;i+=40){ctx.beginPath();ctx.moveTo(0,i);ctx.lineTo(canvas.width,i);ctx.stroke();}

  clouds.forEach(c=>{
    if(gameState==='playing'){c.x-=c.speed*(gameSpeed*0.08); if(c.x<-100) c.x=canvas.width+60;}
    drawCloud(c);
  });
  drawGround();
  if(gameState==='playing') groundOffset+=gameSpeed;
  dino.draw();

  const fs = Math.max(10, canvas.width*0.022);

  if(gameState==='playing') {
    dino.update();
    nextObstacle--;
    if(nextObstacle<=0){
      spawnObstacle();
      nextObstacle=Math.max(Math.floor(80+Math.random()*60-gameSpeed*2),35);
    }
    obstacles.forEach(o=>{ o.x-=gameSpeed; drawCactus(o); });
    obstacles=obstacles.filter(o=>o.x+o.w>-10);

    scoreTimer++;
    if(scoreTimer >= 3) { score++; scoreTimer=0; }

    if(score%100===0 && score>0 && score!==lastSpeedUp){
      lastSpeedUp=score; gameSpeed*=1.1;
      playBeep(660,0.1); setTimeout(()=>playBeep(880,0.15),100);
    }
    txt('SKOR: '+score, 14, fs+6, fs, '#00ff88', 'left');
    txt('EN YUK: '+hiScore, canvas.width-14, fs+6, fs, '#ffffff55', 'right');
    if(checkCollision()){
      gameState='gameover';
      if(score>hiScore) hiScore=score;
      playBeep(300,0.15,'sawtooth',0.2);
      setTimeout(()=>playBeep(200,0.3,'sawtooth',0.2),150);
      try{window.parent.postMessage({type:'DINO_SCORE',score:score},'*');}catch(e){}
    }
  } else if(gameState==='waiting') {
    ctx.fillStyle='rgba(0,0,0,0.5)'; ctx.fillRect(0,0,canvas.width,canvas.height);
    const fs2=Math.max(10,canvas.width*0.028);
    txt('DINO OYUNU', canvas.width/2, canvas.height/2-fs2*1.5, fs2, '#00ff88', 'center');
    txt('SPACE veya TIKLA', canvas.width/2, canvas.height/2+fs2*0.5, fs2*0.65, '#fff', 'center');
    txt('baslamak icin', canvas.width/2, canvas.height/2+fs2*1.8, fs2*0.55, '#ffffff66', 'center');
  } else if(gameState==='gameover') {
    obstacles.forEach(o=>drawCactus(o));
    txt('SKOR: '+score, 14, fs+6, fs, '#00ff88', 'left');
    txt('EN YUK: '+hiScore, canvas.width-14, fs+6, fs, '#ffffff55', 'right');
    ctx.fillStyle='rgba(0,0,0,0.6)'; ctx.fillRect(0,0,canvas.width,canvas.height);
    const fs2=Math.max(10,canvas.width*0.028);
    txt('OYUN BITTI!', canvas.width/2, canvas.height/2-fs2*1.5, fs2, '#ff6b6b', 'center');
    txt('SKOR: '+score, canvas.width/2, canvas.height/2+fs2*0.3, fs2*0.75, '#00ff88', 'center');
    txt('TIKLA veya SPACE - TEKRAR', canvas.width/2, canvas.height/2+fs2*2, fs2*0.55, '#ffffff77', 'center');
  }

  requestAnimationFrame(gameLoop);
}

function handleAction() {
  initAudio();
  if(gameState==='waiting'||gameState==='gameover'){
    gameState='playing'; dino.reset();
    score=0; scoreTimer=0; gameSpeed=3; lastSpeedUp=0;
    obstacles=[]; nextObstacle=80;
  } else { dino.jump(); }
}

document.addEventListener('keydown', e=>{
  if(e.code==='Space'||e.code==='ArrowUp'){e.preventDefault();handleAction();}
});
canvas.addEventListener('touchstart', e=>{ e.preventDefault(); handleAction(); },{passive:false});
canvas.addEventListener('mousedown', ()=>handleAction());

dino.reset();
gameLoop();
</script>
</body>
</html>"""

col1, col2 = st.columns([3, 1])
with col1:
    components.html(GAME_HTML, height=320, scrolling=False)

with col2:
    st.markdown("### Skor Kaydet")
    player_name = st.text_input("Ismin:", placeholder="Adini gir...", max_chars=15)
    manual_score = st.number_input("Skorum:", min_value=0, max_value=99999, step=1)
    if st.button("Kaydet", use_container_width=True):
        if player_name.strip():
            save_score(player_name.strip(), int(manual_score))
            st.success(f"Kaydedildi! {player_name}: {manual_score}")
            st.rerun()
        else:
            st.warning("Isim gir!")

st.markdown("---")
st.markdown("### En Yuksek Skorlar")
df = load_scores()
if df.empty:
    st.info("Henuz skor yok!")
else:
    df_display = df.reset_index(drop=True)
    df_display.index += 1
    st.dataframe(df_display, use_container_width=True, hide_index=True)
