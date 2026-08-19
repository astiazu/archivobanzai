/* ============================================================
   ARCHIVO BAN ZAI · app.js v6
   · Radio aleatoria al arrancar
   · Listas de usuario ("Escuchar")
   · Secciones independientes (la música no se corta)
   · Carrusel álbum infinito
   · Votos, plays, ranking
   ============================================================ */

const API = '';
const $  = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

function ytEmbed(url){
  const m = (url || '').match(/(?:youtu\.be\/|v=|shorts\/|embed\/)([\w-]{11})/);
  return m ? `https://www.youtube-nocookie.com/embed/${m[1]}` : url;
}
function spEmbed(url){ return (url || '').replace('open.spotify.com/', 'open.spotify.com/embed/'); }
function embedFor(i){
  return (i.source === 'spotify' || i.source_type === 'spotify') ? spEmbed(i.url) : ytEmbed(i.url);
}
function ytThumb(url){
  const m = (url || '').match(/(?:youtu\.be\/|v=|shorts\/|embed\/)([\w-]{11})/);
  return m ? `https://i.ytimg.com/vi/${m[1]}/hqdefault.jpg` : null;
}

/* ============ COUNTDOWN ============ */
(function countdown(){
  const target = new Date('2026-09-01T00:00:00').getTime();
  const el  = id => document.getElementById(id);
  const pad = n  => String(n).padStart(2, '0');
  function tick(){
    const diff = target - Date.now();
    if (!el('cd-days')) return;
    if (diff < 0){
      const c = el('countdown');
      if (c) c.innerHTML = '<div style="grid-column:1/-1;font-family:\'Bebas Neue\';font-size:36px;color:#d4af37">¡Ban Zai volvió!</div>';
      return;
    }
    el('cd-days').textContent  = pad(Math.floor(diff / 86400000));
    el('cd-hours').textContent = pad(Math.floor(diff % 86400000 / 3600000));
    el('cd-mins').textContent  = pad(Math.floor(diff % 3600000 / 60000));
    el('cd-secs').textContent  = pad(Math.floor(diff % 60000 / 1000));
  }
  tick();
  setInterval(tick, 1000);
})();

/* ============ ESTADO GLOBAL ============ */
let timeline = [], queue = [], qi = -1, playing = false;
let currentTrackId = null, pendingTrack = null;
let yearAyer = null, yearRadio = null;
let album = [], albumOffset = 0, albumTimer = null;
let listeningUser = null;
const audio = new Audio();

function setPlayerMeta(t, kicker){
  const tt = $('#trackTitle'), tm = $('#trackMeta'), k = $('.player-kicker');
  if (tt) tt.textContent = t.title;
  if (tm) tm.textContent = (t.artist || '') + (t.style ? ' · ' + t.style : '');
  if (k && kicker) k.textContent = kicker;
}
function updatePlayBtn(){
  const b = $('#playBtn'); if (!b) return;
  b.textContent = playing ? '❚❚' : '▶';
  b.classList.toggle('pulse', !playing && !!(pendingTrack || audio.src));
  const d = $('.disc'); if (d) d.classList.toggle('playing', playing);
}
function bumpPlays(t){ fetch(API + '/api/play/' + t.id, { method: 'POST' }); }

/* ============ ARRANQUE: secciones independientes ============ */
async function initTimeline(){
  try { timeline = await (await fetch(API + '/api/timeline')).json(); }
  catch(e){ timeline = []; }

  const rawYears = timeline.map(i => i.year);
  const hasAlways = rawYears.some(y => !y);
  const years = [...new Set(rawYears.filter(Boolean))].sort();
  const html = (hasAlways ? '<button data-year="siempre">SIEMPRE</button>' : '') +
               years.map(y => `<button data-year="${y}">${y}</button>`).join('')
            || '<span class="muted">Todavía no hay material aprobado.</span>';

  const slider = $('#yearSlider'), tags = $('#yearTags');
  if (slider) slider.innerHTML = html;
  if (tags)   tags.innerHTML   = html;

  if (slider) slider.addEventListener('click', e => {
    const b = e.target.closest('button[data-year]'); if (b) selectYearAyer(b.dataset.year);
  });
  if (tags) tags.addEventListener('click', e => {
    const b = e.target.closest('button[data-year]'); if (b) selectYearRadio(b.dataset.year);
  });

  /* Ayer y Hoy: primer año con material */
  const firstAyer = hasAlways ? 'siempre' : years[0];
  if (firstAyer) selectYearAyer(firstAyer);

  /* Radio: AÑO ALEATORIO entre los que tienen tracks */
  const trackYears = [...new Set(timeline.filter(i => i.tipo === 'track').map(i => i.year || 'siempre'))].sort();
  const firstRadio = trackYears.length
    ? trackYears[Math.floor(Math.random() * trackYears.length)]
    : firstAyer;
  if (firstRadio) selectYearRadio(firstRadio);

  initAlbum();
  fillVoces();
  loadRanking();
}

function selectYearAyer(year){
  yearAyer = year;
  $$('#yearSlider button').forEach(b => b.classList.toggle('active', b.dataset.year === year));
  renderAyer(year);
}
function selectYearRadio(year){
  yearRadio = year;
  $$('#yearTags button').forEach(b => b.classList.toggle('active', b.dataset.year === year));
  loadRadio(year);
}

/* ============ AYER Y HOY: MINIATURAS + LIGHTBOX ============ */
function renderAyer(year){
  const v = $('#ayerViewer'); if (!v) return;
  const items = timeline.filter(i => (year === 'siempre' && !i.year) || i.year === year);
  if (!items.length){ v.innerHTML = '<p class="muted">Sin material para este filtro.</p>'; return; }
  v.innerHTML = items.map((i, idx) => {
    let media = '', cls = 'ayer-thumb';
    if (i.tipo === 'video'){
      const t = (i.source !== 'file') ? ytThumb(i.url) : null;
      media = `<div class="thumb-media">${t ? `<img src="${t}" alt="">` : `<video src="${API}${i.file}" muted preload="metadata"></video>`}</div>`;
      cls += ' has-play';
    } else if (i.tipo === 'foto' || i.tipo === 'flyer'){
      media = `<div class="thumb-media"><img src="${API}${i.file}" alt=""></div>`;
    } else if (i.tipo === 'track'){
      media = `<div class="thumb-audio">◉</div>`;
      cls += ' has-play';
    } else {
      media = `<div class="thumb-text">${(i.story || i.title || '').slice(0, 90)}</div>`;
    }
    return `<div class="${cls}" data-idx="${idx}">${media}<b>${i.title || i.tipo}</b><span>${i.year || ''}</span></div>`;
  }).join('');
  v.onclick = e => {
    const c = e.target.closest('.ayer-thumb'); if (!c) return;
    openAyer(items[+c.dataset.idx]);
  };
}

function openAyer(i){
  const body = $('#ayerModalBody');
  if (i.tipo === 'video'){
    body.innerHTML = i.source === 'file'
      ? `<video controls autoplay src="${API}${i.file}" style="width:100%;aspect-ratio:16/9;background:#000"></video>`
      : `<iframe src="${ytEmbed(i.url)}" allowfullscreen allow="autoplay" style="width:100%;aspect-ratio:16/9;border:0"></iframe>`;
  } else if (i.tipo === 'foto' || i.tipo === 'flyer'){
    body.innerHTML = `<img src="${API}${i.file}" style="max-width:100%;max-height:70vh;display:block;margin:auto">`;
  } else if (i.tipo === 'track'){
    body.innerHTML = i.source === 'file'
      ? `<div style="padding:20px"><audio controls autoplay src="${API}${i.file}" style="width:100%"></audio><p style="margin-top:12px;color:#f4f1ea">${i.title} — ${i.artist || ''}</p></div>`
      : `<iframe src="${embedFor(i)}" allowfullscreen style="width:100%;aspect-ratio:16/9;border:0"></iframe>`;
  } else {
    body.innerHTML = `<div style="padding:20px"><p style="font-size:16px;color:#f4f1ea">${i.story || ''}</p></div>`;
  }
  $('#ayerModal').showModal();
}

const closeAyer = $('#closeAyer');
if (closeAyer) closeAyer.addEventListener('click', () => $('#ayerModal').close());
const ayerModal = $('#ayerModal');
if (ayerModal) ayerModal.addEventListener('close', () => { $('#ayerModalBody').innerHTML = ''; });

/* ============ RADIO ============ */
async function loadRadio(year){
  /* Si estamos escuchando una lista de usuario, NO sobreescribir la cola */
  if (listeningUser){
    const np = $('#nowPlaying');
    if (np) np.innerHTML = `Escuchando la lista de <b>${listeningUser}</b> <button id="exitUserList" class="btn btn-ghost" style="padding:4px 10px;margin-left:10px;font-size:11px">Volver a la radio por año</button>`;
    const exit = $('#exitUserList');
    if (exit) exit.addEventListener('click', () => {
      listeningUser = null;
      if (yearRadio) selectYearRadio(yearRadio);
    });
    return;
  }

  let data = { tracks: [], playlists: [] };
  try { data = await (await fetch(API + '/api/radio/' + year)).json(); } catch(e){}

  const newQueue = data.tracks.filter(t => t.source === 'file');
  queue = newQueue;
  qi = (currentTrackId != null) ? newQueue.findIndex(t => t.id === currentTrackId) : -1;
  renderQueue();

  const grid = $('#trackGrid');
  if (grid){
    grid.innerHTML = data.tracks.length ? data.tracks.map((t, i) => `
      <div class="track-card" data-uploader="${t.uploader}">
        <span>${t.source === 'file' ? 'MEZCLA PROPIA' : t.source.toUpperCase()} · ${t.style || 'SIN ESTILO'}</span>
        <b>${t.title}</b>
        <span>${t.artist || ''}</span>
        <span class="uploader">👤 ${t.uploader} · ${t.plays || 0} plays</span>
        <div class="vote-box">
          <button class="btn vote-btn" data-track="${t.id}" data-value="1">👍 <span class="score">${t.score}</span></button>
          <button class="btn vote-btn" data-track="${t.id}" data-value="-1">👎</button>
        </div>
        <button class="btn" data-idx="${i}">${t.source === 'file' ? '▶ Sonar en el player' : '▶ Ver / escuchar'}</button>
      </div>`).join('')
      : '<p class="muted">Sin temas cargados para este filtro.</p>';

    grid.onclick = e => {
      const b = e.target.closest('button[data-idx]');
      const v = e.target.closest('.vote-btn');
      if (b){
        const t = data.tracks[+b.dataset.idx];
        if (t.source === 'file') selectFileTrack(t);
        else showEmbed(t);
      }
      if (v){
        if (!window.BZ || !window.BZ.logged_in){ showVoteGate(); return; }
        fetch(API + '/api/vote/' + v.dataset.track, {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ value: +v.dataset.value })
        }).then(r => r.json()).then(d => {
          if (d.error){ showVoteGate(); return; }
          const s = v.closest('.vote-box').querySelector('.score');
          if (s) s.textContent = d.score;
        });
      }
    };
  }

  const picker = $('#trackPicker');
  if (picker){
    picker.dataset.tracks = JSON.stringify(data.tracks);
    picker.innerHTML = `<option value="">Elegí un tema…</option>` +
      data.tracks.map((t, i) => `<option value="${i}">${t.title}${t.artist ? ' — ' + t.artist : ''}</option>`).join('');
  }

  const ep = $('#embedPanel');
  if (ep) ep.innerHTML = data.playlists.length ? data.playlists.map(p =>
    `<div class="embed-card"><span>${p.source_type === 'spotify' ? 'SPOTIFY' : 'YOUTUBE'} · LISTA DEL EQUIPO</span><b>${p.title}</b><iframe src="${embedFor(p)}" loading="lazy"></iframe></div>`
  ).join('') : '<p class="muted">Sin listas preparadas.</p>';

  const np = $('#nowPlaying');
  if (np) np.textContent = year === 'siempre' ? 'Ban Zai · Sin año' : 'Ban Zai ' + year;

  /* ARRANQUE: TRACK ALEATORIO + intento de autoplay */
  if (currentTrackId == null && queue.length){
    loadTrack(Math.floor(Math.random() * queue.length));
    tryAutoplay();
  }
}

/* Autoplay legal: intenta al cargar; si el navegador lo bloquea,
   arranca con el PRIMER CLICK del usuario en cualquier parte */
function tryAutoplay(){
  const attempt = () => audio.play()
    .then(() => { playing = true; setPlayerMeta(queue[qi], 'SONANDO AHORA'); updatePlayBtn(); })
    .catch(() => {});
  attempt();
  const once = () => {
    setTimeout(() => { if (!playing && currentTrackId != null) attempt(); }, 0);
    document.removeEventListener('click', once);
  };
  document.addEventListener('click', once);
}

/* Elegir tema SIN cortar el que suena */
function selectFileTrack(t){
  if (!playing && !audio.src){
    const q = queue.findIndex(x => x.id === t.id);
    if (q >= 0) loadTrack(q);
    else { qi = -1; currentTrackId = t.id; audio.src = API + t.file; }
    play();
    bumpPlays(t);
  } else if (currentTrackId === t.id){
    playing ? pause() : play();
  } else {
    pendingTrack = t;
    setPlayerMeta(t, 'LISTO PARA SONAR · ▶ PARA CAMBIAR');
    updatePlayBtn();
  }
}

function showEmbed(t){
  $('#embedNow').innerHTML = `
    <iframe src="${embedFor(t)}" allowfullscreen style="aspect-ratio:16/9;width:100%;border:0"></iframe>
    <div style="margin-top:10px;padding:12px;background:#11111a;border:1px solid #222230;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
      <span style="font-family:'Space Grotesk',monospace;font-size:11px;color:#a8a49a">◉ ${t.title} ${t.artist ? '— ' + t.artist : ''}</span>
      <a href="${t.url}" target="_blank" rel="noopener" class="btn" style="padding:8px 16px">Abrir en YouTube ↗</a>
    </div>`;
  $('#embedNow').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/* ============ PLAYER ============ */
function loadTrack(i){
  if (!queue.length) return;
  qi = i;
  const t = queue[qi];
  currentTrackId = t.id;
  pendingTrack = null;
  setPlayerMeta(t, 'LISTO PARA SONAR');
  audio.src = API + t.file;
  renderQueue();
}
function renderQueue(){
  const pl = $('#playlistList'); if (!pl) return;
  pl.innerHTML = queue.map((t, i) => `<div class="${i === qi ? 'active' : ''}">${i === qi ? '▶ ' : ''}${t.title}</div>`).join('')
    || '<div class="muted">Sin mezclas propias en este filtro.</div>';
}
function play(){
  if (pendingTrack){
    const t = pendingTrack;
    qi = queue.findIndex(x => x.id === t.id);
    currentTrackId = t.id;
    pendingTrack = null;
    setPlayerMeta(t, 'SONANDO AHORA');
    audio.src = API + t.file;
    renderQueue();
    bumpPlays(t);
  }
  if (!audio.src){ if (queue.length) loadTrack(0); else return; }
  audio.play().catch(() => {});
  playing = true;
  updatePlayBtn();
}
function pause(){
  audio.pause(); playing = false;
  updatePlayBtn();
}
function next(){ if (queue.length){ loadTrack(qi < 0 ? 0 : (qi + 1) % queue.length); play(); } }
function prev(){ if (queue.length){ loadTrack(qi < 0 ? 0 : (qi - 1 + queue.length) % queue.length); play(); } }

audio.addEventListener('ended', next);
audio.addEventListener('timeupdate', () => {
  const p = $('#progress');
  if (p && audio.duration) p.style.width = (audio.currentTime / audio.duration * 100) + '%';
});

const playBtn = $('#playBtn');
if (playBtn) playBtn.addEventListener('click', () => playing ? pause() : play());
const nextBtn = $('#nextBtn'); if (nextBtn) nextBtn.addEventListener('click', next);
const prevBtn = $('#prevBtn'); if (prevBtn) prevBtn.addEventListener('click', prev);

const picker = $('#trackPicker');
if (picker) picker.addEventListener('change', () => {
  if (picker.value === '') return;
  const t = JSON.parse(picker.dataset.tracks)[picker.value];
  if (t.source === 'file') selectFileTrack(t);
  else showEmbed(t);
});

/* ============ RANKING ============ */
async function loadRanking(){
  let d = { top_tracks: [], top_users: [] };
  try { d = await (await fetch(API + '/api/ranking')).json(); } catch(e){}
  const tt = $('#topTracks');
  if (tt) tt.innerHTML = d.top_tracks.length ? d.top_tracks.map(t =>
    `<li><div><b>${t.title}</b><span>${t.artist || ''} · 👤 ${t.uploader}</span></div><em>👍 ${t.score} · ${t.plays} ▶</em></li>`).join('')
    : '<li class="muted">Sin votos todavía. ¡Sé el primero en votar!</li>';
  const tu = $('#topUsers');
  if (tu) tu.innerHTML = d.top_users.length ? d.top_users.map(u =>
    `<li>
       <div>
         <b>${u.username}</b>
         <span>${u.score} 👍 · ${u.tracks} aportes</span>
       </div>
       <button class="btn btn-playlist" data-user="${u.username}">▶ Escuchar</button>
     </li>`).join('')
    : '<li class="muted">Sin aportes todavía.</li>';

  /* Delegación de click: botón Escuchar de cada usuario */
  if (tu){
    tu.querySelectorAll('.btn-playlist').forEach(b => {
      b.addEventListener('click', () => listenToUser(b.dataset.user));
    });
  }
}

/* ============ ÁLBUM: CARRUSEL INFINITO ============ */
function initAlbum(){
  album = timeline.filter(i => (i.tipo === 'foto' || i.tipo === 'flyer') && i.file);
  if (!album.length) return;
  renderAlbum();
  albumTimer = setInterval(() => { albumOffset++; renderAlbum(); }, 6000);
  const stop = () => { if (albumTimer){ clearInterval(albumTimer); albumTimer = null; } };
  const prev = $('#albumPrev'), next = $('#albumNext');
  if (prev) prev.addEventListener('click', () => { stop(); albumOffset--; renderAlbum(); });
  if (next) next.addEventListener('click', () => { stop(); albumOffset++; renderAlbum(); });
}
function renderAlbum(){
  const tiles = [$('.memory-a'), $('.memory-b'), $('.memory-c'), $('.memory-d'), $('.memory-e')];
  const n = album.length;
  if (!n) return;
  tiles.forEach((t, i) => {
    if (!t) return;
    const pos = (((albumOffset + i) % n) + n) % n;
    const f = album[pos];
    t.style.backgroundImage    = `url(${API}${f.file})`;
    t.style.backgroundSize     = 'cover';
    t.style.backgroundPosition = 'center';
    const b = t.querySelector('b');
    if (b) b.textContent = (f.title || 'RECUERDO BAN ZAI').toUpperCase();
    const s = t.querySelector('span');
    if (s && i < 4) s.textContent = 'FOTO / ' + String(pos + 1).padStart(3, '0');
  });
}

/* ============ VOCES ============ */
function fillVoces(){
  const hist = timeline.find(i => (i.tipo === 'historia' || i.tipo === 'audio') && i.story);
  const bq = document.querySelector('.quote blockquote');
  if (hist && bq){
    bq.textContent = '"' + hist.story.slice(0, 220) + (hist.story.length > 220 ? '…' : '') + '"';
    const p = document.querySelector('.quote p');
    if (p) p.textContent = '— ' + (hist.title || 'Voz de la comunidad') + (hist.year ? ' · ' + hist.year : '');
  }
}

/* ============ MODAL SUBIR RECUERDO (REAL) ============ */
const uploadBtn = $('#uploadDemo'), dialog = $('#demoDialog');
if (uploadBtn) uploadBtn.addEventListener('click', () => {
  if (!window.BZ || !window.BZ.logged_in){
    showGate('Para subir tu recuerdo primero sumate a la comunidad.');
    return;
  }
  const du = $('#dialogUser');
  if (du) du.textContent = 'Conectado como ' + window.BZ.username + '. Tu aporte entra a moderación del equipo.';
  dialog.showModal();
});
const closeBtn = $('#closeDialog'); if (closeBtn) closeBtn.addEventListener('click', () => dialog.close());

/* Según el tipo de material, muestra/oculta archivo y URL */
const kindSelect = $('#kindSelect');
if (kindSelect) kindSelect.addEventListener('change', () => {
  const k = kindSelect.value;
  $('#fileLabel').style.display = (k === 'historia') ? 'none' : '';
  $('#urlLabel').style.display  = (k === 'video') ? '' : 'none';
  $('#recuerdoFile').required   = (k !== 'historia' && k !== 'video');
});

/* Envío real al backend */
const recuerdoForm = $('#recuerdoForm');
if (recuerdoForm) recuerdoForm.addEventListener('submit', async e => {
  e.preventDefault();
  const msg = $('#dialogMessage');
  if (!$('#authCheck').checked){ msg.textContent = '⚠️ Debés autorizar la publicación del material.'; return; }
  const kind = kindSelect.value;
  const file = $('#recuerdoFile').files[0];
  const url  = (recuerdoForm.source_url.value || '').trim();
  if (kind !== 'historia' && kind !== 'video' && !file){ msg.textContent = '⚠️ Adjuntá el archivo (foto, audio o flyer).'; return; }
  if (kind === 'video' && !file && !url){ msg.textContent = '⚠️ Para video: adjuntá un archivo o pegá una URL de YouTube.'; return; }

  const fd = new FormData(recuerdoForm);
  if (!file) fd.delete('file');
  msg.textContent = 'Enviando…';
  try {
    const r = await fetch(API + '/api/recuerdos', { method: 'POST', body: fd });
    const d = await r.json();
    if (d.ok){
      msg.textContent = d.status === 'aprobado'
        ? '✓ ¡Gracias! Tu recuerdo ya está publicado.'
        : '✓ ¡Gracias! Tu recuerdo entró a moderación y el equipo lo publica.';
      recuerdoForm.reset();
      setTimeout(() => dialog.close(), 2500);
    } else {
      msg.textContent = '⚠️ ' + (d.error || 'No se pudo enviar.');
    }
  } catch(err){
    msg.textContent = '⚠️ Error de conexión. Probá de nuevo.';
  }
});

/* ============ ESCUCHAR LISTA DE USUARIO ============ */
function listenToUser(username){
  listeningUser = username;
  const userTracks = timeline.filter(i => i.tipo === 'track' && i.uploader === username && i.source === 'file');
  if (!userTracks.length){ alert('Este usuario todavía no tiene mezclas propias.'); return; }

  queue = userTracks;
  loadTrack(Math.floor(Math.random() * queue.length));
  play();
  bumpPlays(queue[qi]);

  /* Mostrar banner "Escuchando a X" */
  const np = $('#nowPlaying');
  if (np) np.innerHTML = `Escuchando la lista de <b>${username}</b> <button id="exitUserList" class="btn btn-ghost" style="padding:4px 10px;margin-left:10px;font-size:11px">Volver a la radio por año</button>`;
  const exit = $('#exitUserList');
  if (exit) exit.addEventListener('click', () => {
    listeningUser = null;
    if (yearRadio) selectYearRadio(yearRadio);
  });

  renderQueue();
  /* Scroll suave al player para que el usuario vea que arrancó */
  $('.radio-player')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/* ============ SESIÓN + GATE DE VOTO ============ */
window.BZ = { logged_in: false };
fetch(API + '/api/me').then(r => r.json()).then(d => { window.BZ = d; }).catch(() => {});

function showGate(msg){
  if ($('#voteGate')) return;
  const g = document.createElement('div');
  g.id = 'voteGate';
  g.innerHTML = `🔐 <b>${msg}</b>
    <a href="/login">Ingresá</a> · <a href="/registro">Creá tu cuenta</a>
    <button id="gateClose" aria-label="Cerrar">✕</button>`;
  document.body.appendChild(g);
  g.querySelector('#gateClose').addEventListener('click', () => g.remove());
}
function showVoteGate(){ showGate('Para votar sumate a la comunidad Ban Zai.'); }

/* ============ OYENTES EN VIVO (heartbeat) ============ */
function sendHeartbeat(){
  fetch(API + '/api/listening', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ track_id: currentTrackId }),
    credentials: 'same-origin'
  }).then(r => r.json()).then(d => {
    const o = $('#statOyentes'), c = $('#statComunidad');
    if (o) o.textContent = d.oyentes;
    if (c) c.textContent = d.comunidad;
  }).catch(() => {});
}
/* Stats al cargar + heartbeat cada 15s (cuando hay audio) */
fetch(API + '/api/stats').then(r => r.json()).then(d => {
  const o = $('#statOyentes'), c = $('#statComunidad');
  if (o) o.textContent = d.oyentes;
  if (c) c.textContent = d.comunidad;
}).catch(() => {});
setInterval(sendHeartbeat, 15000);

/* ============ CARRUSEL PROTAGONISTAS ============ */
(async function(){
  const track = document.getElementById('protTrack');
  if (!track) return;
  const r = await fetch(API + '/api/protagonistas');
  const protas = await r.json();
  track.innerHTML = protas.map(p => `
    <div class="card-protagonista" data-id="${p.id}">
      <div class="role">${p.role}</div>
      <h3>${p.name}</h3>
      <div class="meta">${p.meta}</div>
      <div class="quote">"${p.quote}"</div>
      <span class="ver-mas">Ver historia completa →</span>
    </div>`).join('');

  const dialog = document.getElementById('protDialog');
  track.addEventListener('click', e => {
    e.preventDefault();
    const card = e.target.closest('.card-protagonista');
    if (!card) return;
    const p = protas.find(x => x.id == card.dataset.id);
    if (!p) return;
    document.getElementById('protRole').textContent = p.role;
    document.getElementById('protName').textContent = p.name;
    document.getElementById('protMeta').textContent = p.meta;
    document.getElementById('protText').textContent = p.text;
    document.getElementById('protQuote').textContent = '"' + p.quote + '"';
    document.getElementById('protSource').textContent = p.source;

    const media = document.getElementById('protMedia');
    let mh = '';
    if (p.media_type === 'foto' && p.media_file)
      mh = '<img src="/uploads/protagonistas/' + p.media_file + '" style="width:100%;border:1px solid #222230">';
    else if (p.media_type === 'video' && p.media_file)
      mh = '<video controls src="/uploads/protagonistas/' + p.media_file + '" style="width:100%"></video>';
    else if (p.media_type === 'video' && p.media_url)
      mh = '<iframe width="100%" height="300" src="https://www.youtube.com/embed/' + (p.media_url.match(/(?:v=|youtu\.be\/)([\w-]{11})/) || [,''])[1] + '" frameborder="0" allowfullscreen></iframe>';
    else if (p.media_type === 'audio' && p.media_file)
      mh = '<audio controls src="/uploads/protagonistas/' + p.media_file + '" style="width:100%"></audio>';
    media.innerHTML = mh;
    const y = window.scrollY;
    dialog.showModal();
    window.scrollTo(0, y);
  });
  document.getElementById('closeProtDialog').onclick = () => {
  dialog.close();
  window.scrollTo(0, window.scrollY);
  };

  const prev = document.getElementById('protPrev');
  const next = document.getElementById('protNext');
  const visibles = () => innerWidth <= 600 ? 1 : innerWidth <= 900 ? 2 : 4;
  const paso = () => (track.querySelector('.card-protagonista').offsetWidth + 16) * visibles();
  prev.onclick = () => track.scrollBy({left: -paso(), behavior: 'smooth'});
  next.onclick = () => track.scrollBy({left: paso(), behavior: 'smooth'});
  const flechas = () => {
    prev.disabled = track.scrollLeft <= 0;
    next.disabled = track.scrollLeft >= track.scrollWidth - track.clientWidth - 5;
  };
  track.addEventListener('scroll', flechas);
  flechas();
})();

/* ============ APORTE DE PROTAGONISTAS (comunidad) ============ */
const btnProta = document.getElementById('btnProta');
const protaDialog = document.getElementById('protaFormDialog');
if (btnProta) btnProta.addEventListener('click', () => {
  if (!window.BZ || !window.BZ.logged_in) {
    showGate('Para contar tu historia primero sumate a la comunidad.');
    return;
  }
  const y = window.scrollY;
  protaDialog.showModal();
  window.scrollTo(0, y);
});
document.getElementById('closeProtaForm').onclick = () => protaDialog.close();

const protaForm = document.getElementById('protaForm');
if (protaForm) protaForm.addEventListener('submit', async e => {
  e.preventDefault();
  const msg = document.getElementById('protaMsg');
  msg.textContent = 'Enviando…';
  const fd = new FormData(protaForm);
  try {
    const r = await fetch(API + '/api/protagonistas', { method: 'POST', body: fd });
    const d = await r.json();
    if (d.ok) {
      msg.textContent = '✓ ¡Gracias! Tu ficha entró a moderación.';
      protaForm.reset();
      setTimeout(() => protaDialog.close(), 2500);
    } else {
      msg.textContent = '⚠️ ' + (d.error || 'No se pudo enviar.');
    }
  } catch (err) {
    msg.textContent = '⚠️ Error de conexión.';
  }
});

/* ============ ARRANQUE ============ */
initTimeline();