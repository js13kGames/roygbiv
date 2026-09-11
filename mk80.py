#!/usr/bin/env python3
"""
Fabrique index-80.html a partir de index.html : la meme partie, rendue
comme une borne d'arcade des annees 80.
  - resolution interne reduite (K), agrandie au plus proche voisin
  - une ligne interne sur deux assombrie (scanlines)
  - police bitmap 3x5 en bits, branchee a la place de fillText
  - fond noir, herbe en pixels
"""
import io, sys, os
SRC, OUT = 'index.html', 'index-80.html'
FONT = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font3x5.txt')).read().strip()
s = io.open(SRC, encoding='utf-8').read()
def rep(a, b):
    global s
    if a not in s: sys.exit("INTROUVABLE: " + a[:70])
    s = s.replace(a, b, 1)

# ---- CSS : agrandissement pixelise, coins arrondis de tube cathodique ----
rep("canvas{display:block;width:100%;height:100%;touch-action:none;user-select:none;",
    "canvas{display:block;width:100%;height:100%;image-rendering:pixelated;image-rendering:crisp-edges;"
    "border-radius:14px;touch-action:none;user-select:none;")
rep("<title>ROYGBIV</title>", "<title>ROYGBIV 80</title>")

# ---- resolution interne : le canvas fait K fois la vue logique ----
rep("""function resize(){ var d=Math.min(2,devicePixelRatio||1);
  C.width=innerWidth*d; C.height=innerHeight*d;
  // le zoom vise une hauteur de vue constante: meme cadrage sur tous les ecrans
  Z=Math.min(1.5,Math.max(0.5,innerHeight/1150));
  W=innerWidth/Z; H=innerHeight/Z; SC=d*Z;""",
"""var K=0.4;                                  // 1 unite logique = 0.4 pixel interne
function resize(){
  Z=Math.min(2.2,Math.max(0.7,innerHeight/800));    // vue plus serree: on voit mieux le heros
  W=innerWidth/Z; H=innerHeight/Z; SC=K;
  C.width=W*K|0; C.height=H*K|0; X.imageSmoothingEnabled=false;""")

# ---- police bitmap 3x5, branchee a la place du texte vectoriel ----
rep("var AW=3000, AH=3000, camX=0, camY=0;        // le monde, et l'oeil qui le suit",
"""var AW=3000, AH=3000, camX=0, camY=0;
// police 3x5: 59 glyphes de l'espace a Z, 15 bits chacun, en base 32
var FONT='""" + FONT + """';
function ptext(t,x,y,fs,c,al){
  t=(''+t).toUpperCase(); var n=t.length, i, b, g,
    px=mx(1,mn(Math.round(fs*K*0.42),(W*K*0.94/(n*4))|0)),   // taille d'un point, en pixels internes
    s=px/K, w=(n*4-1)*s;
  x=Math.round((x-(al==='center'?w/2:al==='right'?w:0))*K)/K; y=Math.round((y-5*s)*K)/K;
  X.fillStyle=c;
  for(i=0;i<n;i++){ g=parseInt(FONT.substr((t.charCodeAt(i)-32)*3,3),32)||0;
    for(b=0;b<15;b++) if(g>>(14-b)&1) X.fillRect(x+i*4*s+(b%3)*s,y+((b/3)|0)*s,s,s); }
  return w;
}
function fsz(){ return parseFloat((X.font.match(/[\\d.]+/)||[12])[0]); }
X.fillText=function(t,x,y){ ptext(t,x,y,fsz(),X.fillStyle,X.textAlign); };
X.strokeText=function(t,x,y){ var f=X.fillStyle; ptext(t,x+1/K,y+1/K,fsz(),OUT,X.textAlign); X.fillStyle=f; };
X.measureText=function(t){ var n=(''+t).length, px=mx(1,mn(Math.round(fsz()*K*0.42),(W*K*0.94/(n*4))|0));
  return {width:(n*4-1)*px/K}; };""")

# ---- rendu : transformation interne, et scanlines a la fin ----
rep("function render(){\n  X.setTransform(SC,0,0,SC,0,0);",
    "function render(){\n  X.setTransform(SC,0,0,SC,0,0); X.imageSmoothingEnabled=false;")
# le hud est la derniere chose dessinee : on accroche les scanlines juste apres
# les scanlines passent en repere interne (transformation identite) : elles
# doivent donc etre la TOUTE derniere chose dessinee, apres les ecrans de
# cartes et de fin, sinon ceux-ci heritent du mauvais repere
rep("""    otext(wdBq[0],W/2,46,19,'#ffd42e',1); X.globalAlpha=1; X.textAlign='left'; }
}
""", """    otext(wdBq[0],W/2,46,19,'#ffd42e',1); X.globalAlpha=1; X.textAlign='left'; }
  scan();
}
// une ligne interne sur deux assombrie, comme un tube cathodique.
// Doit etre la derniere chose dessinee: elle repasse en repere interne.
function scan(){ X.setTransform(1,0,0,1,0,0); X.fillStyle='rgba(0,0,0,0.22)';
  for(var sl=1;sl<C.height;sl+=2) X.fillRect(0,sl,C.width,1); }
""")
# l'ecran titre sort tot: il lui faut son propre appel
rep("""    drawTitle(); X.restore(); return; }""",
    """    drawTitle(); X.restore(); scan(); return; }""")

# ---- le noir de l'arcade ----
rep("var BG='#3f7a55';", "var BG='#000';")
rep("html,body{margin:0;height:100%;background:#160a26;", "html,body{margin:0;height:100%;background:#000;")
# l'herbe : deux pixels verts au lieu de brins traces
rep("""    if(k===2){                                         // une touffe d'herbe
      X.lineCap='round'; X.lineWidth=2.6; X.strokeStyle='#356b48'; X.beginPath();
      for(var j=-2;j<3;j++){ X.moveTo(j*3.4,3); X.quadraticCurveTo(j*4,-3,j*5+1,-9); }
      X.stroke();
      X.lineWidth=1.3; X.strokeStyle='#63b078'; X.stroke();
      X.restore(); continue; }""",
"""    if(k===2){                                         // une touffe: trois pixels
      X.fillStyle='#1c6b3a'; X.fillRect(-5,-5,5,5); X.fillRect(2,-8,5,5);
      X.fillStyle='#3fb56a'; X.fillRect(-2,-2,3,3);
      X.restore(); continue; }""")
# la vignette est deja la; le halo du champ passe en gris froid
rep("  lgd.addColorStop(0,'rgba(255,210,255,0.10)');", "  lgd.addColorStop(0,'rgba(180,220,255,0.08)');")

io.open(OUT, 'w', encoding='utf-8').write(s)
print("%s ecrit (%d octets)" % (OUT, len(s)))

# =====================================================================
# Une borne de 1985 n'a ni halo ni degrade : on les retire, et ce sont
# eux qui payent la police bitmap et les scanlines.
# =====================================================================
import re
s = io.open(OUT, encoding='utf-8').read()
# plus aucun flou d'ombre
s = re.sub(r"X\.shadowColor=[^;]+;\s*X\.shadowBlur=[^;]+;", "", s)
s = re.sub(r"\s*X\.shadowBlur=0;", "", s)
s = re.sub(r"if\(w\)\{\s*\}\s*else X\.rotate", "if(!w) X.rotate", s)
# le halo au sol sous le heros
s = s.replace("""  var lgd=X.createRadialGradient(P.x,P.y,0,P.x,P.y,230);
  lgd.addColorStop(0,'rgba(180,220,255,0.08)'); lgd.addColorStop(1,'rgba(0,0,0,0)');
  X.fillStyle=lgd; X.fillRect(P.x-230,P.y-230,460,460);
""", "")
# la vignette
s = s.replace("""  var vg=X.createRadialGradient(W/2,H/2,mn(W,H)*0.35,W/2,H/2,mx(W,H)*0.75);
  vg.addColorStop(0,'rgba(0,0,0,0)'); vg.addColorStop(1,'rgba(9,28,18,0.72)');
  X.fillStyle=vg; X.fillRect(0,0,W,H);
""", "")
# le bouton du joystick : un disque plat
s = s.replace("""      var jg=X.createRadialGradient(jx,jy-8,2,jx,jy,29);
      jg.addColorStop(0,'#fff'); jg.addColorStop(1,BAND[mx(0,lit-1)]);
      X.fillStyle=jg;""", "      X.fillStyle=BAND[mx(0,lit-1)];")
# le ciel du titre : noir plat, les etoiles suffisent
s = s.replace("""  var g=X.createRadialGradient(cx,H/2,60,cx,H/2,mx(W,H)*0.85);
  g.addColorStop(0,'#241040'); g.addColorStop(1,'#12061f');
  X.fillStyle=g; X.fillRect(0,0,W,H);""", "  X.fillStyle='#000'; X.fillRect(0,0,W,H);")
# le cone de lumiere : un trapeze plat
s = s.replace("""  var lg=X.createLinearGradient(0,0,0,H);
  lg.addColorStop(0,'rgba(255,240,200,0.18)'); lg.addColorStop(1,'rgba(255,240,200,0)');
  X.fillStyle=lg;""", "  X.fillStyle='rgba(255,240,200,0.09)';")
io.open(OUT, 'w', encoding='utf-8').write(s)
print("halos et degrades retires")

# =====================================================================
# Coupes propres a la version arcade
# =====================================================================
s = io.open(OUT, encoding='utf-8').read()
# les noms de pouvoirs en 9px sur la pile de bandes sont illisibles en
# bitmap et deborderaient : la pile reste, coloree, sans texte
s = s.replace("""    if(bi<lit&&slot[bi]>=0){ X.fillStyle='rgba(0,0,0,0.75)'; X.font='bold 9px monospace'; X.textAlign='left';
      X.fillText(UP[slot[bi]][0],bx+5,by+i*(bh+3)+10); }
    else if(bi<lvl&&slot[bi]>=0){ X.fillStyle='rgba(255,255,255,0.35)'; X.font='bold 9px monospace'; X.textAlign='left';
      X.fillText(UP[slot[bi]][0],bx+5,by+i*(bh+3)+10); } }""", "  }")
# la bordure du monde : la carte reduite suffit

# le texte flottant ne se met plus a l'echelle : les pixels resteraient
# irreguliers. Il monte et s'efface, c'est tout.
s = s.replace("""  for(i=0;i<texts.length;i++){ var tp=texts[i], b=1-tp.l, z=tp.z*Math.pow(sin(b*PI),0.5);
    X.save(); X.translate(tp.x+tp.dx*b,tp.y-18-34*b); X.rotate(b*tp.r); X.scale(z,z);
    otext(tp.t,0,0,15,tp.c,1); X.restore(); }""",
"""  for(i=0;i<texts.length;i++){ var tp=texts[i], b=1-tp.l;
    X.globalAlpha=mn(1,tp.l*2.5); otext(tp.t,tp.x,tp.y-18-34*b,14*tp.z,tp.c,1); }
  X.globalAlpha=1;""")
# otext : plus de trait a regler, le bitmap fait l'ombre lui-meme
s = s.replace("""function otext(t,x,y,fs,c,bold){
  X.font=(bold?'bold ':'')+(fs|0)+'px monospace'; X.textAlign='center';
  X.lineWidth=fs*0.22; X.lineJoin='round'; X.strokeStyle=OUT;
  X.strokeText(t,x,y); X.fillStyle=c; X.fillText(t,x,y);
}""",
"""function otext(t,x,y,fs,c){ X.font=fs+'px m'; X.textAlign='center';
  X.strokeText(t,x,y); X.fillStyle=c; X.fillText(t,x,y); }""")
io.open(OUT, 'w', encoding='utf-8').write(s)
print("coupes arcade appliquees")

# le spectre qui gonfle et les etoiles tournantes sont des effets de
# lissage : en gros pixels ils deviennent des taches. On garde l'onde,
# la gerbe de particules et la tete qui vole.
s = io.open(OUT, encoding='utf-8').read()
s = s.replace("""  // le spectre de la bete, qui gonfle et s'efface
  pops.push({x:e.x,y:e.y,t:e.t,f:e.face,l:0.32,L:0.32});
  for(var sp2=0;sp2<5;sp2++){ var sa=rnd()*TAU, ss=rr(60,190);
    stars.push({x:e.x,y:e.y,vx:cos(sa)*ss,vy:sin(sa)*ss,l:rr(0.3,0.6),
      r:rr(4,9),c:sp2%2?'#fff':ET[e.t][3],rot:rnd()*TAU}); }
""", "")
s = s.replace("""  for(var pi=pops.length-1;pi>=0;pi--){ pops[pi].l-=dt;
    if(pops[pi].l<=0) pops.splice(pi,1); }
  for(var si=stars.length-1;si>=0;si--){ var sr=stars[si];
    sr.l-=dt; sr.x+=sr.vx*dt; sr.y+=sr.vy*dt; sr.vx*=0.93; sr.vy*=0.93;
    sr.rot+=dt*6; if(sr.l<=0) stars.splice(si,1); }
""", "")
s = s.replace("""  // le spectre des licornes qui viennent de mourir
  X.save(); X.globalCompositeOperation='lighter';
  for(i=0;i<pops.length;i++){ var po=pops[i], kp=1-po.l/po.L, es=eSpr[po.t],
      pw=es.width*eScl[po.t]*(1+kp*1.1), ph=es.height*eScl[po.t]*(1+kp*1.1);
    X.globalAlpha=(1-kp)*0.75;
    X.save(); X.translate(po.x,po.y); X.scale(po.f,1);
    X.drawImage(es,-pw/2,-ph/2,pw,ph); X.restore(); }
  X.restore();
  // les etoiles de la gerbe
  X.save(); X.globalCompositeOperation='lighter';
  for(i=0;i<stars.length;i++){ var sr=stars[i];
    X.globalAlpha=mn(1,sr.l*2.6);
    X.save(); X.translate(sr.x,sr.y); X.rotate(sr.rot);
    spark(0,0,sr.r,sr.c); X.restore(); }
  X.restore();
""", "")
s = s.replace("var rings=[], gibs=[], pops=[], stars=[], texts=[], freeze=0, dim=0;",
              "var rings=[], gibs=[], texts=[], freeze=0, dim=0;")
s = s.replace("  rings=[]; gibs=[]; pops=[]; stars=[]; texts=[]; freeze=0;",
              "  rings=[]; gibs=[]; texts=[]; freeze=0;")
io.open(OUT, 'w', encoding='utf-8').write(s)
print("spectres et etoiles retires")

# =====================================================================
# Corrections de texte
#  - Safari renvoie la police normalisee avec le poids en chiffres
#    ('700 30px monospace') : il faut lire le nombre colle a 'px'.
#  - la taille des points suit un facteur plus sobre, et l'interligne
#    suit la hauteur reelle des glyphes bitmap.
#  - le titre se dessine en un seul appel, une couleur par lettre, pour
#    que le retrecissement automatique voie les sept lettres.
# =====================================================================
s = io.open(OUT, encoding='utf-8').read()
s = s.replace("""function ptext(t,x,y,fs,c,al){
  t=(''+t).toUpperCase(); var n=t.length, i, b, g,
    px=mx(1,mn(Math.round(fs*K*0.42),(W*K*0.94/(n*4))|0)),   // taille d'un point, en pixels internes
    s=px/K, w=(n*4-1)*s;
  x=Math.round((x-(al==='center'?w/2:al==='right'?w:0))*K)/K; y=Math.round((y-5*s)*K)/K;
  X.fillStyle=c;
  for(i=0;i<n;i++){ g=parseInt(FONT.substr((t.charCodeAt(i)-32)*3,3),32)||0;
    for(b=0;b<15;b++) if(g>>(14-b)&1) X.fillRect(x+i*4*s+(b%3)*s,y+((b/3)|0)*s,s,s); }
  return w;
}
function fsz(){ return parseFloat((X.font.match(/[\\d.]+/)||[12])[0]); }""",
"""// taille d'un point en pixels internes, pour une police fs et n caracteres
function ppx(fs,n){ return mx(1,mn(Math.round(fs*K*0.32),(W*K*0.94/(n*4))|0)); }
function ptext(t,x,y,fs,c,al){
  t=(''+t).toUpperCase(); var n=t.length, i, b, g, px=ppx(fs,n), s=px/K, w=(n*4-1)*s;
  x=Math.round((x-(al==='center'?w/2:al==='right'?w:0))*K)/K; y=Math.round((y-5*s)*K)/K;
  for(i=0;i<n;i++){ g=parseInt(FONT.substr((t.charCodeAt(i)-32)*3,3),32)||0;
    X.fillStyle=Array.isArray(c)?c[i%c.length]:c;
    for(b=0;b<15;b++) if(g>>(14-b)&1) X.fillRect(x+i*4*s+(b%3)*s,y+((b/3)|0)*s,s,s); }
  return w;
}
// le nombre colle a 'px', pas le premier venu: Safari ecrit '700 30px'
function fsz(){ return parseFloat((X.font.match(/([\\d.]+)px/)||[0,12])[1]); }""")
s = s.replace("""X.measureText=function(t){ var n=(''+t).length, px=mx(1,mn(Math.round(fsz()*K*0.42),(W*K*0.94/(n*4))|0));
  return {width:(n*4-1)*px/K}; };""",
"""X.measureText=function(t){ var n=(''+t).length; return {width:(n*4-1)*ppx(fsz(),n)/K}; };""")

# le titre : un appel, sept couleurs
s = s.replace("""  var fs=mn(120,W/6.2)|0, y=H*0.44;
  X.font='bold '+fs+'px monospace'; X.textAlign='left';
  var ti='ROYGBIV', ox=cx-X.measureText(ti).width/2;
  for(i=0;i<7;i++){ var ch=ti.charAt(i), cw=X.measureText(ch).width;
    X.lineWidth=fs*0.16; X.lineJoin='round'; X.strokeStyle=OUT; X.strokeText(ch,ox,y);
     X.fillStyle=BAND[i];
    X.fillText(ch,ox,y); ox+=cw; }
""",
"""  var fs=mn(120,W/6.2)|0, y=H*0.44;
  ptext('ROYGBIV',cx+1/K,y+1/K,fs,OUT,'center');
  ptext('ROYGBIV',cx,y,fs,BAND,'center');
""")
# les taglines : interligne = 1.3 fois la hauteur reelle des glyphes
s = s.replace("  var f=mn(26,W/16), l=f*1.3; y+=mn(40,W/14);",
              "  var f=mn(26,W/16), l=5*ppx(f,25)/K*1.3; y+=l*1.1;")
# l'ecran de fin : les quatre lignes s'espacent d'apres leur hauteur
s = s.replace("""  X.font='bold '+(mn(38,W/(t.length*0.66))|0)+'px monospace'; X.fillText(t,cx,cy+m*0.06);
  X.fillStyle='rgba(255,255,255,0.5)'; X.font=(mn(14,W/28)|0)+'px monospace';
  X.fillText(sub,cx,cy+m*0.06+24);""",
"""  var ty=cy+m*0.06, th=5*ppx(38,t.length)/K;
  X.font='38px m'; X.fillText(t,cx,ty);
  X.fillStyle='rgba(255,255,255,0.5)'; X.font='14px m';
  X.fillText(sub,cx,ty+th*0.9);""")
s = s.replace("""  X.fillStyle='#fff'; X.font='bold '+(mn(16,W/24)|0)+'px monospace';
  X.fillText(kills+' unicorns    '+(T|0)+'s    band '+lvl+'/7',cx,cy+m*0.12+34);""",
"""  X.fillStyle='#fff'; X.font='16px m';
  X.fillText(kills+' unicorns    '+(T|0)+'s    band '+lvl+'/7',cx,cy+m*0.12+52);""")
s = s.replace("""  X.font=(mn(13,W/30)|0)+'px monospace';
  X.fillText(isTouch?'tap to go again':'click to go again',cx,cy+m*0.12+62);""",
"""  X.font='13px m';
  X.fillText(isTouch?'tap to go again':'click to go again',cx,cy+m*0.12+92);""")
# les cartes : la description descend sous le nom
s = s.replace("    X.fillText(UP[u][1],r[0]+68,r[1]+56);", "    X.fillText(UP[u][1],r[0]+68,r[1]+62);")
io.open(OUT, 'w', encoding='utf-8').write(s)
print("textes corriges")

# =====================================================================
# Une taille commune par bloc de lignes, et des titres qui tiennent
# =====================================================================
s = io.open(OUT, encoding='utf-8').read()
# le plancher etait trop strict : a 2 pixels, 25 caracteres tiennent dans 212
s = s.replace("(W*K*0.94/(n*4))|0", "(W*K*0.98/(n*4))|0")
# le texte peut etre borne par une largeur locale (les cartes), pas seulement l'ecran
s = s.replace("function ppx(fs,n){ return mx(1,mn(Math.round(fs*K*0.32),(W*K*0.98/(n*4))|0)); }",
  "var TXW=0;   // largeur maximale locale pour le texte, 0 = tout l'ecran\n"
  "function ppx(fs,n){ return mx(1,mn(Math.round(fs*K*0.32),((TXW||W*0.98)*K/(n*4))|0)); }")
# ptext accepte une taille de point imposee (fp) : meme taille pour tout un bloc
s = s.replace("function ptext(t,x,y,fs,c,al){\n  t=(''+t).toUpperCase(); var n=t.length, i, b, g, px=ppx(fs,n), s=px/K, w=(n*4-1)*s;",
              "function ptext(t,x,y,fs,c,al,fp){\n  t=(''+t).toUpperCase(); var n=t.length, i, b, g, px=fp||ppx(fs,n), s=px/K, w=(n*4-1)*s;")
# les taglines : un seul point-taille pour les quatre lignes, cale sur la plus
# longue. La hauteur rendue en bitmap vaut 1.6 fois la taille nominale, alors
# qu'une police vectorielle en fait 0.7 : les bornes verticales sont donc
# resserrees ici pour que le paysage tienne.
s = s.replace("var fs=mn(120,W/6.2,H*0.16)|0,", "var fs=mn(120,W/6.2,H*0.1)|0,")
s = s.replace("""  var f=mn(26,W/16,H*0.045), l=f*1.35; y+=f*1.6;
  otext('EVERYONE LOVES UNICORNS.',cx,y,f,'#fff');
  otext('NOBODY WRITES A GOOD PART',cx,y+l,f,'#fff');
  otext('FOR THE RAINBOW.',cx,y+l*2,f,'#fff');
  otext('THAT CHANGES TONIGHT.',cx,y+l*3.3,f,'#ffd42e',1);""",
"""  var tp=ppx(mn(26,W/16,H*0.03),25), l=5*tp/K*1.35; y+=l*1.2;
  [['EVERYONE LOVES UNICORNS.','#fff'],['NOBODY WRITES A GOOD PART','#fff'],
   ['FOR THE RAINBOW.','#fff'],['THAT CHANGES TONIGHT.','#ffd42e']].forEach(function(q,j){
    var yy=y+l*(j>2?j+0.3:j);
    ptext(q[0],cx+1/K,yy+1/K,0,OUT,'center',tp); ptext(q[0],cx,yy,0,q[1],'center',tp); });
  var by=y+l*3.9;""")
s = s.replace("  var by=y+l*3.6, av=H-52-by,", "  var av=H-52-by,")
# les cartes : nom a 2 points, description a 1 point (rapport 2:1 des interfaces 8 bits)
s = s.replace("X.font='bold 20px monospace';\n    X.fillText(UP[u][0],r[0]+68,r[1]+34);",
              "X.font='14px m';\n    X.fillText(UP[u][0],r[0]+68,r[1]+34);")
s = s.replace("X.font='13px monospace';\n    X.fillText(UP[u][1],r[0]+68,r[1]+62);",
              "X.font='8px m';\n    X.fillText(UP[u][1],r[0]+68,r[1]+58);")
# les titres de fin : courts, pour rester gros sur 212 pixels de large
s = s.replace("endScreen('YOU GOT YOUR COLOURS BACK','nobody is laughing now')",
              "endScreen('COLOURS BACK','nobody is laughing now')")
io.open(OUT, 'w', encoding='utf-8').write(s)
print("blocs de texte homogenes")

# =====================================================================
# Les cartes : le texte se borne a la largeur de la carte
# =====================================================================
s = io.open(OUT, encoding='utf-8').read()
s = s.replace("""    icon(r[0]+40,r[1]+r[3]/2,15,UP[u][2],BAND[lvl]);
    X.textAlign='left'; X.fillStyle=BAND[lvl]; X.font='14px m';
    X.fillText(UP[u][0],r[0]+68,r[1]+34);
    X.fillStyle='rgba(255,255,255,0.72)'; X.font='8px m';
    X.fillText(UP[u][1],r[0]+68,r[1]+58);""",
"""    icon(r[0]+28,r[1]+r[3]/2,13,UP[u][2],BAND[lvl]);
    TXW=r[2]-62; X.textAlign='left'; X.fillStyle=BAND[lvl]; X.font='14px m';
    X.fillText(UP[u][0],r[0]+50,r[1]+34);
    X.fillStyle='rgba(255,255,255,0.72)'; X.font='8px m';
    X.fillText(UP[u][1],r[0]+50,r[1]+58); TXW=0;""")
io.open(OUT, 'w', encoding='utf-8').write(s)
print("cartes bornees")

# =====================================================================
# spark() ne servait plus qu'a une seule forme d'icone depuis le retrait
# des etoiles de mort. On la remplace par un losange et on jette la
# fonction : cinq courbes de Bezier pour un dessin de 26 pixels, en gros
# pixels ca ne se voyait de toute facon pas.
# =====================================================================
s = io.open(OUT, encoding='utf-8').read()
s = s.replace("  else if(k<4){ X.restore(); spark(x,y,r,c); return; }                // etincelle",
              "  else if(k<4){ X.moveTo(0,-r); X.lineTo(r*0.45,0); X.lineTo(0,r);\n    X.lineTo(-r*0.45,0); }                                            // losange fin")
i = s.index("function spark(x,y,r,c){")
j = s.index("\n", s.index("X.quadraticCurveTo(x,y,x,y-r); X.fill(); }", i))
s = s[:i] + s[j+1:]
io.open(OUT, 'w', encoding='utf-8').write(s)
print("spark supprimee de la version arcade")

# =====================================================================
# icon() : huit formes vectorielles distinctes pour une pastille de cinq
# pixels de cote, personne ne les distingue. Un carre plein a la couleur
# de la bande, avec un liseré clair, se lit mieux et coute dix fois moins.
# =====================================================================
s = io.open(OUT, encoding='utf-8').read()
i = s.index("function icon(x,y,r,k,c){")
j = s.index("\n}\n", i)
s = s[:i] + """function icon(x,y,r,k,c){
  var d=r*1.4;
  X.fillStyle=OUT; X.fillRect(x-d/2-2,y-d/2-2,d+4,d+4);
  X.fillStyle=c; X.fillRect(x-d/2,y-d/2,d,d);
  X.fillStyle='rgba(255,255,255,0.45)'; X.fillRect(x-d/2,y-d/2,d,d/3);
}""" + s[j+3:]
io.open(OUT, 'w', encoding='utf-8').write(s)
print("icones simplifiees")
