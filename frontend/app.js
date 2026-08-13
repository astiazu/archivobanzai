/* ============================================================
   ARCHIVO BANZAI · app.js v3 (definitivo)
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

/* ============ 1) COUNTDOWN ============ */
(function countdown(){
  const target = new Date('2026-09-01T00:00:00').getTime();
  const el  = id => document.getElementById(id);
  const pad = n  => String(n).padStart(2, '0');
  function tick(){
    const diff = target - Date.now();
    if (!el('cd-days')) return;
    if (diff < 0){
      const c = el('countdown');
      if (c) c.innerHTML = '<div style="grid-column:1/-1;font-family:\'Bebas Neue\';font-size:36px;color:#d4af37">¡BanZai volvió!</div>';
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

/* ============ 2) TIMELINE + RADIO ============ */
let timeline = [], queue = [], qi = 0, playing = false;
const audio = new Audio();

async function initTimeline(){
  try { timeline = await (await fetch(API + '/api/timeline')).json(); }
  catch(e){ console.error('Timeline error:', e); timeline = []; }

  const rawYears = timeline.map(i => i.year);
  const hasAlways = rawYears.some(y => !y);
  const years = [...new Set(rawYears.filter(Boolean))].sort();
  const html = (hasAlways ? '<button data-year="siempre">SIEMPRE</button>' : '') +
               years.map(y => `<button data-year="${y}">${y}</button>`).join('')
            || '<span class="muted">Todavía no hay material aprobado.</span>';

  const slider = $('#yearSlider'), tags = $('#yearTags');
  if (slider) slider.innerHTML = html;
  if (tags)   tags.innerHTML   = html;
  const click = e => { const b = e.target.closest('button[data-year]'); if (b) selectYear(b.dataset.year); };
  if (slider) slider.addEventListener('click', click);
  if (tags)   tags.addEventListener('click', click);

  fillMosaic();
  fillVoces();
}

function selectYear(year){
  $$('#yearSlider button, #yearTags button').forEach(b => b.classList.toggle('active', b.dataset.year === year));
  renderAyer(year);
  loadRadio(year);
}

function ytThumb(url){
  const m = (url || '').match(/(?:youtu\.be\/|v=|shorts\/|embed\/)([\w-]{11})/);
  return m ? `https://i.ytimg.com/vi/${m[1]}/hqdefault.jpg` : null;
}

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

/* Lightbox: abre el reproductor completo al hacer click */
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

async function loadRadio(year){
  let data = { tracks: [], playlists: [] };
  try { data = await (await fetch(API + '/api/radio/' + year)).json(); } catch(e){}

  queue = data.tracks.filter(t => t.source === 'file');

  /* TARJETAS DE TODOS LOS TRACKS */
  const grid = $('#trackGrid');
  if (grid){
    grid.innerHTML = data.tracks.length ? data.tracks.map((t, i) => `
      <div class="track-card">
        <span>${t.source === 'file' ? 'MEZCLA PROPIA' : t.source.toUpperCase()} · ${t.style || 'SIN ESTILO'}</span>
        <b>${t.title}</b>
        <span>${t.artist || ''}</span>
        <button class="btn" data-idx="${i}">${t.source === 'file' ? '▶ Sonar en el player' : '▶ Ver / escuchar'}</button>
      </div>`).join('')
      : '<p class="muted">Sin temas cargados para este filtro.</p>';
    grid.onclick = e => {
      const b = e.target.closest('button[data-idx]'); if (!b) return;
      const t = data.tracks[+b.dataset.idx];
      if (t.source === 'file'){
        const q = queue.indexOf(t);
        if (q >= 0) loadTrack(q);
        else { audio.src = API + t.file; $('#trackTitle').textContent = t.title; $('#trackMeta').textContent = t.artist || ''; }
        play();
      } else {
        $('#embedNow').innerHTML = `
          <iframe src="${embedFor(t)}" allowfullscreen style="aspect-ratio:16/9;width:100%;border:0"></iframe>
          <div style="margin-top:10px;padding:12px;background:#11111a;border:1px solid #222230;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
            <span style="font-family:'Space Grotesk',monospace;font-size:11px;color:#a8a49a">◉ ${t.title} ${t.artist ? '— ' + t.artist : ''}</span>
            <a href="${t.url}" target="_blank" rel="noopener" class="btn" style="padding:8px 16px">Abrir en YouTube ↗</a>
          </div>`;
        $('#embedNow').scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };
  }

  /* SELECTOR DE TEMA PUNTUAL */
  const picker = $('#trackPicker');
  if (picker){
    picker.dataset.tracks = JSON.stringify(data.tracks);
    picker.innerHTML = `<option value="">Elegí un tema…</option>` +
      data.tracks.map((t, i) => `<option value="${i}">${t.title}${t.artist ? ' — ' + t.artist : ''}</option>`).join('');
  }

  /* LISTAS DEL EQUIPO */
  const ep = $('#embedPanel');
  if (ep) ep.innerHTML = data.playlists.length ? data.playlists.map(p =>
    `<div class="embed-card"><span>${p.source_type === 'spotify' ? 'SPOTIFY' : 'YOUTUBE'} · LISTA DEL EQUIPO</span><b>${p.title}</b><iframe src="${embedFor(p)}" loading="lazy"></iframe></div>`
  ).join('') : '<p class="muted">Sin listas preparadas.</p>';

  const np = $('#nowPlaying');
  if (np) np.textContent = year === 'siempre' ? 'BanZai · Sin año' : 'BanZai ' + year;

  if (queue.length) loadTrack(0);
  else { const tt = $('#trackTitle'); if (tt) tt.textContent = 'Sin mezclas propias'; }
  renderQueue();
}

function loadTrack(i){
  qi = i;
  const t = queue[qi];
  const tt = $('#trackTitle'), tm = $('#trackMeta');
  if (tt) tt.textContent = t.title;
  if (tm) tm.textContent = (t.artist || '') + (t.style ? ' · ' + t.style : '');
  audio.src = API + t.file;
  renderQueue();
}
function renderQueue(){
  const pl = $('#playlistList'); if (!pl) return;
  pl.innerHTML = queue.map((t, i) => `<div class="${i === qi ? 'active' : ''}">${i === qi ? '▶ ' : ''}${t.title}</div>`).join('');
}
function play(){
  if (!audio.src) return;
  audio.play().catch(() => {});
  playing = true;
  const b = $('#playBtn'); if (b) b.textContent = '❚❚';
  const d = $('.disc');    if (d) d.classList.add('playing');
}
function pause(){
  audio.pause(); playing = false;
  const b = $('#playBtn'); if (b) b.textContent = '▶';
  const d = $('.disc');    if (d) d.classList.remove('playing');
}

audio.addEventListener('ended', () => { if (queue.length){ loadTrack((qi + 1) % queue.length); play(); } });
audio.addEventListener('timeupdate', () => {
  const p = $('#progress');
  if (p && audio.duration) p.style.width = (audio.currentTime / audio.duration * 100) + '%';
});

const playBtn = $('#playBtn');
if (playBtn) playBtn.addEventListener('click', () => playing ? pause() : play());
const nextBtn = $('#nextBtn');
if (nextBtn) nextBtn.addEventListener('click', () => { if (queue.length){ loadTrack((qi + 1) % queue.length); play(); } });
const prevBtn = $('#prevBtn');
if (prevBtn) prevBtn.addEventListener('click', () => { if (queue.length){ loadTrack((qi - 1 + queue.length) % queue.length); play(); } });

const picker = $('#trackPicker');
if (picker) picker.addEventListener('change', () => {
  if (picker.value === '') return;
  const t = JSON.parse(picker.dataset.tracks)[picker.value];
  if (t.source === 'file'){
    audio.src = API + t.file;
    $('#trackTitle').textContent = t.title;
    $('#trackMeta').textContent  = t.artist || '';
    play();
  } else {
    const en = $('#embedNow');
    if (en) en.innerHTML = `<iframe src="${embedFor(t)}" allowfullscreen></iframe>`;
  }
});

/* ============ 3) MOSAICO Y VOCES ============ */
function fillMosaic(){
  const fotos = timeline.filter(i => (i.tipo === 'foto' || i.tipo === 'flyer') && i.file);
  const tiles = $$('.memory');
  fotos.slice(0, 4).forEach((f, i) => {
    const t = tiles[i]; if (!t) return;
    t.style.backgroundImage    = `url(${API}${f.file})`;
    t.style.backgroundSize     = 'cover';
    t.style.backgroundPosition = 'center';
    const b = t.querySelector('b'); if (b && f.title) b.textContent = f.title.toUpperCase();
  });
}
function fillVoces(){
  const hist = timeline.find(i => (i.tipo === 'historia' || i.tipo === 'audio') && i.story);
  const bq = document.querySelector('.quote blockquote');
  if (hist && bq){
    bq.textContent = '"' + hist.story.slice(0, 220) + (hist.story.length > 220 ? '…' : '') + '"';
    const p = document.querySelector('.quote p');
    if (p) p.textContent = '— ' + (hist.title || 'Voz de la comunidad') + (hist.year ? ' · ' + hist.year : '');
  }
}

/* ============ 4) MODAL ============ */
const uploadBtn = $('#uploadDemo'), dialog = $('#demoDialog');
if (uploadBtn) uploadBtn.addEventListener('click', () => dialog.showModal());
const closeBtn = $('#closeDialog'); if (closeBtn) closeBtn.addEventListener('click', () => dialog.close());
const sendBtn = $('#sendDemo');
if (sendBtn) sendBtn.addEventListener('click', () => {
  $('#dialogMessage').textContent = '✓ Recibido. En la versión real entra a moderación.';
  setTimeout(() => dialog.close(), 1500);
});

/* ============ ARRANQUE ============ */
initTimeline();