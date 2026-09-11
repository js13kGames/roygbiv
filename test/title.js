// L'ecran titre ne doit rien chevaucher, en portrait comme en paysage.
var fs=require('fs');
var FILE=process.argv[2]||'index.html', BITMAP=FILE.indexOf('80')>=0;
var L=[], HERO=null, HEADS=[];
function C(){this.globalAlpha=1;this._f='12px monospace';this.fillStyle='#fff';this.textAlign='left';this.imageSmoothingEnabled=true}
Object.defineProperty(C.prototype,'font',{get(){return this._f},set(v){this._f=v.replace(/^bold /,'700 ')}});
['rotate','beginPath','arc','arcTo','moveTo','lineTo','closePath','fill','stroke','clearRect','clip','ellipse','rect','quadraticCurveTo','bezierCurveTo','strokeRect','setLineDash','fillRect'].forEach(m=>C.prototype[m]=function(){});
// etat de transformation PAR CONTEXTE: chaque sprite est cuit dans le sien
C.prototype.save=function(){ (this._st=this._st||[]).push([this._x||0,this._y||0,this._s||1]); };
C.prototype.restore=function(){ var v=(this._st||[]).pop();
  if(v){ this._x=v[0]; this._y=v[1]; this._s=v[2]; } };
C.prototype.translate=function(x,y){ this._x=(this._x||0)+x*(this._s||1); this._y=(this._y||0)+y*(this._s||1); };
C.prototype.scale=function(a){ this._s=(this._s||1)*a; };
C.prototype.setTransform=function(){ this._x=0; this._y=0; this._s=1; this._st=[]; };
C.prototype.drawImage=function(im){ if(this===MAIN&&im&&im.oy!==undefined){ var s=this._s||1;
  LAST={top:this._y-im.oy*s, bot:this._y+(im.height-im.oy)*s}; } };
C.prototype.fillText=function(t,x,y){ if(!BITMAP) L.push([(''+t).slice(0,26),y,parseFloat(this._f.match(/([\d.]+)px/)[1])]); };
C.prototype.strokeText=function(){};
C.prototype.createRadialGradient=C.prototype.createLinearGradient=()=>({addColorStop(){}});
C.prototype.measureText=function(t){ var px=parseFloat(this._f.match(/([\d.]+)px/)[1]); return {width:(''+t).length*px*0.62}; };
var MAIN=null;
function E(){this.width=300;this.height=150;this.style={};
  this.getContext=function(){ var c=new C(); if(!MAIN) MAIN=c; return c; };
  this.addEventListener=()=>{}}
global.document={createElement:()=>new E(),getElementById:()=>new E(),addEventListener(){},body:new E()};
global.window=global; global.self=global; global.devicePixelRatio=3;
global.addEventListener=()=>{}; global.requestAnimationFrame=()=>0;
global.setInterval=()=>0; global.setTimeout=()=>0;
global.AudioContext=global.webkitAudioContext=function(){throw 0};
var LAST=null;

[[390,844,'portrait'],[844,390,'paysage'],[430,932,'grand portrait'],[1920,1080,'desktop']].forEach(function(f){
  global.innerWidth=f[0]; global.innerHeight=f[1];
  var src=fs.readFileSync(FILE,'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
  if(BITMAP) src=src.replace('function ptext(t,x,y,fs,c,al,fp){',
    'function ptext(t,x,y,fs,c,al,fp){ if(c!==OUT) globalThis.__L.push([(""+t).slice(0,26),y,5*(fp||ppx(fs,(""+t).length))/K]);');
  src+=';globalThis.__A={render:render,K:'+(BITMAP?'K':'1')+',dim:function(){return [W,H]},heroY:function(){return 0}};';
  globalThis.__L=[]; L=[]; LAST=null; MAIN=null;
  (0,eval)(src);
  var A=globalThis.__A, d=A.dim();
  A.render();
  var lines=BITMAP?globalThis.__L.map(function(l){return [l[0],l[1],l[2]];})
                  :L.map(function(l){return [l[0],l[1],l[2]*1.0];});
  // le heros : dernier drawImage avec une origine
  var hero=LAST;
  var prev=-1e9, pb=0, out=[];
  lines.forEach(function(l){ var top=l[1]-l[2];
    var bad=(top<prev-1 && l[0].length>1); if(bad) pb++;
    out.push('    '+String(l[0]).padEnd(26)+' de '+String(top.toFixed(0)).padStart(5)+' a '+String(l[1].toFixed(0)).padStart(5)+(bad?'  CHEVAUCHE':''));
    prev=l[1]; });
  var hs='';
  if(hero){ var chevH=lines.some(function(l){ return l[1]>hero.top && l[1]-l[2]<hero.bot; });
    if(chevH) pb++;
    hs=' | heros de '+hero.top.toFixed(0)+' a '+hero.bot.toFixed(0)+(chevH?'  CHEVAUCHE LE TEXTE':'')
       +(hero.bot>d[1]?'  HORS ECRAN':''); }
  if(pb) process.exitCode=1;
  console.log('  titre '+(f[2]+'            ').slice(0,15)+' vue '+Math.round(d[0])+'x'+Math.round(d[1])+hs+'  -> '+(pb?pb+' PROBLEMES':'ok'));
  if(pb) out.forEach(function(o){ console.log(o); });
});
