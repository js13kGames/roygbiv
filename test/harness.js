// Faux DOM commun aux tests : canvas, audio et boucle d'animation simules.
// Le contexte imite Safari, qui renvoie la police normalisee avec le poids en
// chiffres ('700 30px monospace'). C'est ce detail qui avait casse la police
// bitmap de la version arcade : elle lisait 700 comme taille de caractere.
const fs = require('fs');

function install(w, h, opts) {
  opts = opts || {};
  function C() {
    this._f = '12px monospace'; this.fillStyle = '#fff'; this.strokeStyle = '#fff';
    this.globalAlpha = 1; this.shadowBlur = 0; this.textAlign = 'left';
    this.lineWidth = 1; this.imageSmoothingEnabled = true;
  }
  Object.defineProperty(C.prototype, 'font', {
    get: function () { return this._f; },
    set: function (v) { this._f = String(v).replace(/^bold /, '700 '); }
  });
  ['save','restore','translate','scale','rotate','beginPath','arc','arcTo','moveTo',
   'lineTo','closePath','fill','stroke','fillRect','clearRect','drawImage','clip',
   'ellipse','rect','quadraticCurveTo','bezierCurveTo','setTransform','strokeRect',
   'setLineDash','fillText','strokeText'].forEach(function (m) {
     C.prototype[m] = function () { if (opts.track) opts.track(m, arguments, this); };
   });
  C.prototype.createRadialGradient = C.prototype.createLinearGradient =
    function () { return { addColorStop: function () {} }; };
  C.prototype.measureText = function (t) {
    var px = parseFloat((this._f.match(/([\d.]+)px/) || [0, 12])[1]);
    return { width: String(t).length * px * 0.62 };
  };
  function El() {
    this.width = 300; this.height = 150; this.style = {};
    this.getContext = function () { return new C(); };
    this.addEventListener = function () {};
    this.getBoundingClientRect = function () { return { width: w, height: h, left: 0, top: 0 }; };
  }
  global.document = { createElement: function () { return new El(); },
                      getElementById: function () { return new El(); },
                      addEventListener: function () {}, body: new El() };
  global.window = global;
  global.self = global;
  global.innerWidth = w; global.innerHeight = h;
  global.devicePixelRatio = opts.dpr || 3;
  global.addEventListener = function () {};
  global.requestAnimationFrame = function () { return 0; };
  global.setInterval = function () { return 0; };
  global.setTimeout = function () { return 0; };
  // pas d'audio : le jeu doit tourner meme si AudioContext echoue
  global.AudioContext = global.webkitAudioContext = function () { throw new Error('no audio'); };
}

// Charge le <script> d'un index.html et expose les symboles demandes.
function load(file, names) {
  var js = fs.readFileSync(file, 'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
  (0, eval)(js + ';globalThis.__G={' + names.map(function (n) {
    return n + ':typeof ' + n + '!="undefined"?' + n + ':null';
  }).join(',') + '};');
  return globalThis.__G;
}

module.exports = { install: install, load: load };
