// Fake DOM shared by the tests: simulated canvas, audio and animation loop.
// The context mimics Safari, which returns the font normalized with a numeric
// weight ('700 30px monospace'). That detail is what broke the bitmap font in
// the arcade version: it read 700 as the character size.
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
  // no audio: the game must run even if AudioContext fails
  global.AudioContext = global.webkitAudioContext = function () { throw new Error('no audio'); };
}

// Loads the <script> from an index.html and exposes the requested symbols.
function load(file, names) {
  var js = fs.readFileSync(file, 'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
  (0, eval)(js + ';globalThis.__G={' + names.map(function (n) {
    return n + ':typeof ' + n + '!="undefined"?' + n + ':null';
  }).join(',') + '};');
  return globalThis.__G;
}

module.exports = { install: install, load: load };
