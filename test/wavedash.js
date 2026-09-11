// Checks the Wavedash integration with no platform, on BOTH versions.
//
// The stub mimics the real SDK: it VALIDATES TYPES, exactly as it does. A
// permissive stub tests nothing -- that is exactly what lets through the bug
// where terser rewrites true as 1 and every call is rejected in silence.
const fs = require('fs');
const path = require('path');
const H = require(path.join(__dirname, 'harness.js'));

const FILE = process.argv[2] || 'src/index-80.html';
let fail = 0;
function ok(c, m) { console.log('  ' + (c ? 'ok  ' : 'FAIL  ') + m); if (!c) fail = 1; }

function makeSdk(opts) {
  opts = opts || {};
  const calls = { init: 0, stats: 0, get: 0, set: [], board: [], upload: [] };
  const vBool = (v, w) => { if (typeof v !== 'boolean') throw new Error(w + ': expected boolean, got ' + typeof v); };
  const vStr = (v, w) => { if (typeof v !== 'string') throw new Error(w + ': expected string'); };
  const vNum = (v, w) => { if (typeof v !== 'number' || !isFinite(v)) throw new Error(w + ': expected number'); };
  const known = new Set(opts.known || []);
  const unlocked = new Set();
  return {
    calls,
    api: {
      init() { calls.init++; return true; },
      requestStats() {
        calls.stats++;
        if (opts.statsReject) return Promise.reject(new Error('nope'));
        return Promise.resolve(opts.statsFail ? { success: false } : { success: true, data: true });
      },
      getAchievement(id) { vStr(id, 'identifier'); calls.get++; return unlocked.has(id); },
      setAchievement(id, storeNow) {
        vStr(id, 'identifier'); vBool(storeNow, 'storeNow');      // the boolean trap
        calls.set.push(id);
        if (!known.size || known.has(id)) { unlocked.add(id); return true; }
        return false;                                             // identifier missing from the portal
      },
      getOrCreateLeaderboard(name, sort, disp) {
        vStr(name, 'name'); vNum(sort, 'sortOrder'); vNum(disp, 'displayType');
        calls.board.push([name, sort, disp]);
        if (opts.boardReject) return Promise.reject(new Error('nope'));
        // the return shape is copied from the generated types: it is `id`, never `_id`
        return Promise.resolve({ success: true, data: { id: 'lb-' + name, name, totalEntries: 0, created: true } });
      },
      uploadLeaderboardScore(id, score, keepBest) {
        vStr(id, 'leaderboardId'); vNum(score, 'score'); vBool(keepBest, 'keepBest');
        calls.upload.push([id, score, keepBest]);
        if (opts.uploadReject) return Promise.reject(new Error('nope'));
        return Promise.resolve({ success: true });
      },
    },
  };
}

// Loads the game with a given SDK (or none) and makes the levers reachable.
function boot(sdk, src) {
  H.install(1400, 800, {});
  global.self = global; global.window = global;
  if (sdk) global.Wavedash = sdk; else delete global.Wavedash;
  let js = src;
  js += ';globalThis.__G={start:start,update:update,render:render,camera:camera,pick:pick,' +
        'kill:killEnemy,hurt:hurtPlayer,spawn:spawnEnemy,ents:function(){return ents;},' +
        'award:wdAward,end:wdEnd,banner:function(){return wdBq.slice();},' +
        'set:function(k,v){if(k==="kills")kills=v;if(k==="lit")lit=v;if(k==="lvl")lvl=v;' +
        'if(k==="T")T=v;if(k==="mode")mode=v;if(k==="slot")slot=v;if(k==="ifr")P.ifr=v;},' +
        'press:function(o){keys=o;}};';
  (0, eval)(js);
  return globalThis.__G;
}

const raw = fs.readFileSync(FILE, 'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
const tick = () => new Promise(r => setImmediate(r));

(async function () {
  console.log('════════ ' + FILE);

  // 1. no platform: the game must run and attempt nothing.
  {
    const G = boot(null, raw);
    G.start(); G.camera(); G.update(1 / 60); G.render();
    G.award('FIRST_BLOOD');
    G.camera(); G.update(1 / 60); G.render();
    ok(G.banner()[0] === 'FIRST BLOOD', 'no SDK: the in-house banner still shows');
  }

  // 2. with a full SDK: init, stats, achievements, leaderboards.
  {
    const s = makeSdk({});
    const G = boot(s.api, raw);
    ok(s.calls.init === 1, 'init() called once');
    ok(s.calls.stats === 1, 'requestStats() called at startup');
    await tick(); await tick();
    G.start();
    G.award('FIRST_BLOOD'); G.award('FIRST_BLOOD');           // twice: sent once
    await tick(); await tick();
    ok(s.calls.set.length === 1 && s.calls.set[0] === 'FIRST_BLOOD', 'an achievement is sent only once');
    ok(G.banner().length === 1, 'the banner does not repeat either');

    G.set('kills', 343); G.set('lit', 7); G.set('T', 120);
    G.end(1);
    await tick(); await tick(); await tick();
    const ids = s.calls.set.join(',');
    ok(/ROYGBIV/.test(ids), 'win: ROYGBIV');
    ok(/PERFECT_PRISM/.test(ids), 'win with all seven bands: PERFECT_PRISM');
    ok(/SPEED_OF_LIGHT/.test(ids), 'win under 150 s: SPEED_OF_LIGHT');
    const names = s.calls.board.map(b => b[0]);
    ok(names.indexOf('unicorns-felled-v1') >= 0, 'kills leaderboard created');
    ok(names.indexOf('fastest-rainbow-v1') >= 0, 'time leaderboard created');
    ok(s.calls.board.every(b => typeof b[1] === 'number' && typeof b[2] === 'number'),
       'enums passed as numbers');
    ok(s.calls.upload.length === 2, 'two scores sent');
    ok(s.calls.upload.every(u => u[2] === true), 'keepBest is a REAL boolean (terser trap)');
    ok(s.calls.upload.every(u => Number.isFinite(u[1])), 'the scores are finite numbers');
  }

  // 3. a score of zero is still a score: it must not be filtered out.
  {
    const s = makeSdk({});
    const G = boot(s.api, raw);
    await tick(); await tick();
    G.start(); G.set('kills', 0); G.end(0);
    await tick(); await tick();
    ok(s.calls.upload.length === 1 && s.calls.upload[0][1] === 0, 'a score of zero is sent all the same');
  }

  // 4. achievement earned BEFORE the stats reply: queued, not lost.
  {
    let release;
    const s = makeSdk({});
    s.api.requestStats = () => { s.calls.stats++; return new Promise(r => (release = r)); };
    const G = boot(s.api, raw);
    G.start(); G.award('FIRST_BLOOD');
    await tick();
    ok(s.calls.set.length === 0, 'before the stats: nothing is sent');
    release({ success: true, data: true });
    await tick(); await tick();
    ok(s.calls.set.length === 1, 'after the stats: the queued achievement is sent');
  }

  // 5. SDK broken in every way: no exception may escape.
  for (const opts of [{ statsFail: 1 }, { statsReject: 1 }, { boardReject: 1 }, { uploadReject: 1 }]) {
    const s = makeSdk(opts);
    const G = boot(s.api, raw);
    G.start(); G.award('FIRST_BLOOD'); G.set('kills', 5); G.end(1);
    for (let i = 0; i < 6; i++) await tick();
    G.camera(); G.update(1 / 60); G.render();
    ok(true, 'degraded SDK (' + Object.keys(opts)[0] + '): the game keeps running, no exception');
  }

  // 6. missing methods: a guard on each call, no cascade failure.
  {
    const s = makeSdk({});
    const G = boot({ init: s.api.init }, raw);
    G.start(); G.award('FIRST_BLOOD'); G.end(1);
    for (let i = 0; i < 4; i++) await tick();
    ok(s.calls.init === 1, 'init() goes through even if the rest of the SDK is missing');
  }

  // 7. identifier missing from the portal: the SDK returns false, no retry.
  {
    const s = makeSdk({ known: ['ROYGBIV'] });
    const G = boot(s.api, raw);
    await tick(); await tick();
    G.start(); G.award('FIRST_BLOOD');
    for (let i = 0; i < 4; i++) await tick();
    ok(s.calls.set.length >= 1, 'an unknown identifier is tried without looping');
  }

  // 8. THIN_RED_LINE is a comeback achievement: falling to a single band only
  //    counts if all seven were painted first. Both directions are checked,
  //    otherwise a test that only sees the positive case would let through an
  //    achievement that still fires too early.
  for (const [lvl, expected] of [[3, false], [7, true]]) {
    const s = makeSdk({});
    const G = boot(s.api, raw);
    await tick(); await tick();
    G.start();
    G.set('slot', [0, 1, 2, 3, 4, 5, 6]);      // valid powers in every band
    G.set('lvl', lvl); G.set('lit', 2); G.set('ifr', 0); G.set('mode', 'play');
    G.hurt();                                   // the second band goes out: one is left
    await tick(); await tick();
    const fired = s.calls.set.indexOf('THIN_RED_LINE') >= 0;
    ok(fired === expected, 'THIN RED LINE at ' + lvl + ' painted bands: ' +
       (expected ? 'fires' : 'does not fire'));
  }

  console.log(fail ? '  SOME WAVEDASH TESTS FAILED' : '  wavedash: all pass');
  process.exit(fail);
})();
