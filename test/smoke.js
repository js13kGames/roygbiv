try{
var fs=require('fs');
function C(){this.globalAlpha=1;this.shadowBlur=0}
['save','restore','translate','scale','rotate','beginPath','arc','arcTo','moveTo','lineTo','closePath','fill','stroke','fillRect','clearRect','drawImage','clip','ellipse','rect','quadraticCurveTo','bezierCurveTo','setTransform','strokeRect','fillText','setLineDash','strokeText'].forEach(m=>C.prototype[m]=function(){});
C.prototype.createRadialGradient=C.prototype.createLinearGradient=()=>({addColorStop(){}});
C.prototype.measureText=()=>({width:8});
function E(){this.width=300;this.height=150;this.style={};this.getContext=()=>new C();this.addEventListener=()=>{}}
global.document={createElement:()=>new E(),getElementById:()=>new E(),addEventListener(){},body:new E()};
global.window=global; global.self=global; global.innerWidth=390; global.innerHeight=844; global.devicePixelRatio=2;
global.addEventListener=()=>{}; global.requestAnimationFrame=()=>0; global.setInterval=()=>0; global.setTimeout=()=>0;
global.AudioContext=global.webkitAudioContext=function(){throw 0};
var FILE=process.argv[2]||'index.html';
var src=fs.readFileSync(FILE,'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
src+=';globalThis.__G={start:start,update:update,render:render,pick:pick,levelUp:levelUp,'+
 'mode:function(){return mode},set:function(k,v){if(k=="mode")mode=v;}};';
(0,eval)(src);
var G=globalThis.__G;
G.render();                                    // ecran titre
G.start();
for(var b=0;b<6;b++){ G.levelUp(); G.render(); G.pick(b%3); }
for(var i=0;i<2000;i++){ G.update(0.016); G.render(); }
G.set('mode','dead'); G.render();
G.set('mode','win');  G.render();
console.log('  smoke : titre, 6 montees, 2000 images, mort et victoire : ok');

}catch(e){ console.log('  smoke : PLANTAGE ->',e.message); process.exit(1); }
