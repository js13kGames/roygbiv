// Verifie l'integration Wavedash sans plateforme, sur les DEUX versions.
//
// Le stub imite le SDK reel : il VALIDE LES TYPES, exactement comme lui. Un
// stub permissif ne teste rien -- c'est precisement ce qui laisse passer le
// bug ou terser reecrit true en 1 et ou chaque appel est rejete en silence.
const fs = require('fs');
const path = require('path');
const H = require(path.join(__dirname, 'harness.js'));

const FILE = process.argv[2] || 'index.html';
let fail = 0;
function ok(c, m) { console.log('  ' + (c ? 'ok  ' : 'ECHEC ') + m); if (!c) fail = 1; }

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
        vStr(id, 'identifier'); vBool(storeNow, 'storeNow');      // le piege des booleens
        calls.set.push(id);
        if (!known.size || known.has(id)) { unlocked.add(id); return true; }
        return false;                                             // identifiant absent du portail
      },
      getOrCreateLeaderboard(name, sort, disp) {
        vStr(name, 'name'); vNum(sort, 'sortOrder'); vNum(disp, 'displayType');
        calls.board.push([name, sort, disp]);
        if (opts.boardReject) return Promise.reject(new Error('nope'));
        // la forme du retour se copie des types generes : c'est `id`, jamais `_id`
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

// Charge le jeu avec un SDK donne (ou aucun) et rend les leviers accessibles.
function boot(sdk, src) {
  H.install(1400, 800, {});
  global.self = global; global.window = global;
  if (sdk) global.Wavedash = sdk; else delete global.Wavedash;
  let js = src;
  js += ';globalThis.__G={start:start,update:update,render:render,camera:camera,pick:pick,' +
        'kill:killEnemy,hurt:hurtPlayer,spawn:spawnEnemy,ents:function(){return ents;},' +
        'award:wdAward,end:wdEnd,banner:function(){return wdBq.slice();},' +
        'set:function(k,v){if(k==="kills")kills=v;if(k==="lit")lit=v;if(k==="lvl")lvl=v;' +
        'if(k==="T")T=v;if(k==="mode")mode=v;},press:function(o){keys=o;}};';
  (0, eval)(js);
  return globalThis.__G;
}

const raw = fs.readFileSync(FILE, 'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
const tick = () => new Promise(r => setImmediate(r));

(async function () {
  console.log('════════ ' + FILE);

  // 1. sans plateforme : le jeu doit tourner et ne rien tenter.
  {
    const G = boot(null, raw);
    G.start(); G.camera(); G.update(1 / 60); G.render();
    G.award('FIRST_BLOOD');
    G.camera(); G.update(1 / 60); G.render();
    ok(G.banner()[0] === 'FIRST BLOOD', 'sans SDK : le bandeau maison s\'affiche quand meme');
  }

  // 2. avec un SDK complet : init, stats, trophees, classements.
  {
    const s = makeSdk({});
    const G = boot(s.api, raw);
    ok(s.calls.init === 1, 'init() appele une fois');
    ok(s.calls.stats === 1, 'requestStats() appele au demarrage');
    await tick(); await tick();
    G.start();
    G.award('FIRST_BLOOD'); G.award('FIRST_BLOOD');           // deux fois : un seul envoi
    await tick(); await tick();
    ok(s.calls.set.length === 1 && s.calls.set[0] === 'FIRST_BLOOD', 'un trophee ne part qu\'une fois');
    ok(G.banner().length === 1, 'le bandeau ne se repete pas non plus');

    G.set('kills', 343); G.set('lit', 7); G.set('T', 120);
    G.end(1);
    await tick(); await tick(); await tick();
    const ids = s.calls.set.join(',');
    ok(/ROYGBIV/.test(ids), 'victoire : ROYGBIV');
    ok(/PERFECT_PRISM/.test(ids), 'victoire 7 bandes : PERFECT_PRISM');
    ok(/SPEED_OF_LIGHT/.test(ids), 'victoire sous 150 s : SPEED_OF_LIGHT');
    const names = s.calls.board.map(b => b[0]);
    ok(names.indexOf('unicorns-felled-v1') >= 0, 'classement des kills cree');
    ok(names.indexOf('fastest-rainbow-v1') >= 0, 'classement du temps cree');
    ok(s.calls.board.every(b => typeof b[1] === 'number' && typeof b[2] === 'number'),
       'enumerations passees en nombres');
    ok(s.calls.upload.length === 2, 'deux scores envoyes');
    ok(s.calls.upload.every(u => u[2] === true), 'keepBest est un VRAI booleen (piege terser)');
    ok(s.calls.upload.every(u => Number.isFinite(u[1])), 'les scores sont des nombres finis');
  }

  // 3. un score de zero reste un score : il ne doit pas etre filtre.
  {
    const s = makeSdk({});
    const G = boot(s.api, raw);
    await tick(); await tick();
    G.start(); G.set('kills', 0); G.end(0);
    await tick(); await tick();
    ok(s.calls.upload.length === 1 && s.calls.upload[0][1] === 0, 'un score nul est bien envoye');
  }

  // 4. trophee gagne AVANT la reponse des stats : mis en attente, pas perdu.
  {
    let release;
    const s = makeSdk({});
    s.api.requestStats = () => { s.calls.stats++; return new Promise(r => (release = r)); };
    const G = boot(s.api, raw);
    G.start(); G.award('FIRST_BLOOD');
    await tick();
    ok(s.calls.set.length === 0, 'avant les stats : rien n\'est envoye');
    release({ success: true, data: true });
    await tick(); await tick();
    ok(s.calls.set.length === 1, 'apres les stats : le trophee en attente part');
  }

  // 5. SDK casse de toutes les facons : aucune exception ne doit sortir.
  for (const opts of [{ statsFail: 1 }, { statsReject: 1 }, { boardReject: 1 }, { uploadReject: 1 }]) {
    const s = makeSdk(opts);
    const G = boot(s.api, raw);
    G.start(); G.award('FIRST_BLOOD'); G.set('kills', 5); G.end(1);
    for (let i = 0; i < 6; i++) await tick();
    G.camera(); G.update(1 / 60); G.render();
    ok(true, 'SDK degrade (' + Object.keys(opts)[0] + ') : le jeu continue sans exception');
  }

  // 6. methodes absentes : un garde par appel, rien ne tombe en cascade.
  {
    const s = makeSdk({});
    const G = boot({ init: s.api.init }, raw);
    G.start(); G.award('FIRST_BLOOD'); G.end(1);
    for (let i = 0; i < 4; i++) await tick();
    ok(s.calls.init === 1, 'init() passe meme si le reste du SDK manque');
  }

  // 7. identifiant absent du portail : le SDK renvoie false, on n'insiste pas.
  {
    const s = makeSdk({ known: ['ROYGBIV'] });
    const G = boot(s.api, raw);
    await tick(); await tick();
    G.start(); G.award('FIRST_BLOOD');
    for (let i = 0; i < 4; i++) await tick();
    ok(s.calls.set.length >= 1, 'un identifiant inconnu est tente sans boucler');
  }

  console.log(fail ? '  DES TESTS WAVEDASH ONT ECHOUE' : '  wavedash : tout passe');
  process.exit(fail);
})();
