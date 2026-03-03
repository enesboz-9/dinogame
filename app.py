import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Dino Oyunu Pro", layout="wide")

# CSS - Retro Tasarım
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
body, .stApp { background: #0d0d1a; color: #e0e0e0; }
h1, h2, h3 { font-family: 'Press Start 2P', monospace !important; color: #00ff88 !important; text-shadow: 2px 2px #000; }
.stDataFrame { border: 1px solid #00ff88; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

SCORES_FILE = "high_scores.csv"

def load_scores():
    if os.path.exists(SCORES_FILE):
        return pd.read_csv(SCORES_FILE)
    return pd.DataFrame(columns=["Isim", "Skor", "Tarih"])

def save_score(name, score):
    if not name or name == "Oyuncu": return # İsimsiz kaydetme
    df = load_scores()
    new_row = pd.DataFrame([{"Isim": name, "Skor": int(score), "Tarih": datetime.now().strftime("%d/%m %H:%M")}])
    df = pd.concat([df, new_row], ignore_index=True)
    df = df.sort_values("Skor", ascending=False).head(10)
    df.to_csv(SCORES_FILE, index=False)

# Skor Takibi (Session State)
if "last_score" not in st.session_state:
    st.session_state.last_score = 0

# JavaScript'ten gelen veriyi yakala
# URL parametreleri veya query_params yerine basit bir form/input simülasyonu
st.title("🦖 Dino Retro")

col1, col2 = st.columns([3, 1])

with col2:
    st.markdown("### Skor Tablosu")
    player_name = st.text_input("Adınız:", value="Oyuncu", max_chars=12)
    
    # JavaScript'ten gelen skoru yakalamak için gizli bir mekanizma
    # Streamlit bileşenleri arasındaki iletişimi yönetir
    data = st.query_params.get("score")
    if data:
        save_score(player_name, data)
        st.query_params.clear()
        st.rerun()

    df = load_scores()
    if not df.empty:
        st.table(df[["Isim", "Skor"]])
    else:
        st.info("Henüz skor yok!")

GAME_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
  body {{ margin:0; background:#0d0d1a; font-family:'Press Start 2P', cursive; overflow:hidden; }}
  canvas {{ display:block; margin: auto; background: #1a1a2e; border: 3px solid #00ff88; }}
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
canvas.width = 800; canvas.height = 250;

let score = 0;
let gameActive = false;
let gameSpeed = 5;
let gravity = 1.2; // Yerçekimi artırıldı
let scoreTimer = 0;

const dino = {{
    x: 50, y: 190, w: 40, h: 40,
    vy: 0, grounded: true,
    jumpForce: -18, // Zıplama gücü dengelendi
    draw() {{
        ctx.fillStyle = '#00ff88';
        ctx.fillRect(this.x, this.y, this.w, this.h);
    }},
    update() {{
        if (!this.grounded) {{
            this.vy += gravity;
            this.y += this.vy;
        }}
        if (this.y >= 190) {{
            this.y = 190;
            this.vy = 0;
            this.grounded = true;
        }}
    }},
    jump() {{
        if (this.grounded) {{
            this.vy = this.jumpForce;
            this.grounded = false;
        }}
    }}
}};

let obstacles = [];
function spawnObstacle() {{
    let h = 30 + Math.random() * 30;
    obstacles.push({{ x: canvas.width, y: 230 - h, w: 20, h: h }});
}}

function reset() {{
    score = 0;
    obstacles = [];
    gameSpeed = 5;
    gameActive = true;
    dino.y = 190;
}}

function loop() {{
    ctx.clearRect(0,0,canvas.width, canvas.height);
    
    // Zemin çizgisi
    ctx.strokeStyle = '#00ff88';
    ctx.beginPath(); ctx.moveTo(0, 230); ctx.lineTo(800, 230); ctx.stroke();

    if (gameActive) {{
        dino.update();
        
        // Skor artışı (Yavaşlatıldı: her 6 karede 1 puan ~ Saniyede 10 puan)
        scoreTimer++;
        if(scoreTimer % 6 === 0) score++;

        if (Math.random() < 0.02) {{
            if (obstacles.length === 0 || obstacles[obstacles.length-1].x < 500) spawnObstacle();
        }}

        obstacles.forEach((o, i) => {{
            o.x -= gameSpeed;
            ctx.fillStyle = '#ff4b4b';
            ctx.fillRect(o.x, o.y, o.w, o.h);

            // Collision
            if (dino.x < o.x + o.w && dino.x + dino.w > o.x && dino.y < o.y + o.h && dino.y + dino.h > o.y) {{
                gameActive = false;
                // Skoru otomatik olarak Streamlit'e gönder
                window.parent.postMessage({{type: 'streamlit:set_query_params', query_params: {{score: score}}}}, '*');
            }}
        }});
        obstacles = obstacles.filter(o => o.x > -20);
        gameSpeed += 0.001;
    }} else {{
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.fillText('BASLAMAK ICIN TIKLA', 400, 120);
    }}

    dino.draw();
    ctx.fillStyle = '#00ff88';
    ctx.textAlign = 'left';
    ctx.fillText('SKOR: ' + score, 20, 30);
    
    requestAnimationFrame(loop);
}}

window.addEventListener('keydown', e => {{ if(e.code === 'Space') {{ e.preventDefault(); gameActive ? dino.jump() : reset(); }} }});
canvas.addEventListener('mousedown', () => {{ gameActive ? dino.jump() : reset(); }});

loop();
</script>
</body>
</html>
"""

with col1:
    components.html(GAME_HTML, height=300)

st.markdown("---")
st.caption("İpucu: Space tuşuyla zıplayabilirsin. Oyun bittiğinde ismin giriliyse skorun otomatik kaydedilir.")
