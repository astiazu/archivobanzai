/* ============ COUNTDOWN A SEPTIEMBRE 2026 ============ */
(function countdown() {
  const target = new Date('2026-09-01T00:00:00').getTime();
  const daysEl = document.getElementById('cd-days');
  const hoursEl = document.getElementById('cd-hours');
  const minsEl = document.getElementById('cd-mins');
  const secsEl = document.getElementById('cd-secs');

  function pad(n) { return String(n).padStart(2, '0'); }

  function tick() {
    const now = Date.now();
    const diff = target - now;
    if (diff < 0) {
      document.getElementById('countdown').innerHTML =
        '<div style="grid-column:1/-1;font-family:\'Bebas Neue\';font-size:36px;color:#d4af37">¡BanZai volvió!</div>';
      return;
    }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    if (daysEl) daysEl.textContent = pad(d);
    if (hoursEl) hoursEl.textContent = pad(h);
    if (minsEl) minsEl.textContent = pad(m);
    if (secsEl) secsEl.textContent = pad(s);
  }
  tick();
  setInterval(tick, 1000);
})();

/* ============ RADIO PLAYER DEMO ============ */
const playlists = {
  '70s': { title: 'BanZai 70s · Disco & Soul', tracks: ['Donna Summer', 'Bee Gees', 'Chic', 'Earth, Wind & Fire'] },
  '80s': { title: 'BanZai 80s · Synth & Pop', tracks: ['Depeche Mode', 'New Order', 'Pet Shop Boys', 'Eurythmics'] },
  '90s': { title: 'BanZai 90s · Dance & House', tracks: ['Corona', 'Haddaway', 'Snap!', 'Reel 2 Real'] },
  '2000s': { title: 'BanZai 2000s · Electro', tracks: ['Daft Punk', 'Modjo', 'Kylie', 'Junior Senior'] },
  'rock': { title: 'Rock Nacional & Internacional', tracks: ['Soda Stereo', 'Sumo', 'Virus', 'The Cure'] },
  'dance': { title: 'Dance Classics', tracks: ['2 Unlimited', 'Culture Beat', 'La Bouche', 'Captain Jack'] },
  'latino': { title: 'Latinos & Tropicales', tracks: ['Juan Luis Guerra', 'Azúcar Moreno', 'Los Pericos', 'Celia Cruz'] },
  'banzai': { title: 'BanZai Memories · Lo más pedido', tracks: ['Black Box', 'Technotronic', 'Soul II Soul', 'Inner City'] },
};

const playBtn = document.getElementById('playBtn');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const trackTitle = document.getElementById('trackTitle');
const trackMeta = document.getElementById('trackMeta');
const nowPlaying = document.getElementById('nowPlaying');
const progress = document.getElementById('progress');
const disc = document.querySelector('.disc');
const playlistList = document.getElementById('playlistList');

let currentKey = null;
let currentTrack = 0;
let playing = false;
let progressInterval = null;

function renderPlaylistList(key) {
  if (!playlistList) return;
  const pl = playlists[key];
  playlistList.innerHTML = '';
  pl.tracks.forEach((t, i) => {
    const div = document.createElement('div');
    div.textContent = (i === currentTrack ? '▶ ' : '  ') + t;
    if (i === currentTrack) div.classList.add('active');
    playlistList.appendChild(div);
  });
}

function load(key) {
  if (!playlists[key]) return;
  currentKey = key;
  currentTrack = 0;
  trackTitle.textContent = playlists[key].title;
  trackMeta.textContent = playlists[key].tracks[0];
  nowPlaying.textContent = playlists[key].title;
  renderPlaylistList(key);
}

function play() {
  if (!currentKey) load('banzai');
  playing = true;
  playBtn.textContent = '❚❚';
  disc.classList.add('playing');
  let p = 0;
  clearInterval(progressInterval);
  progressInterval = setInterval(() => {
    p += 1;
    if (p >= 100) {
      p = 0;
      currentTrack = (currentTrack + 1) % playlists[currentKey].tracks.length;
      trackMeta.textContent = playlists[currentKey].tracks[currentTrack];
      renderPlaylistList(currentKey);
    }
    progress.style.width = p + '%';
  }, 200);
}

function pause() {
  playing = false;
  playBtn.textContent = '▶';
  disc.classList.remove('playing');
  clearInterval(progressInterval);
}

if (playBtn) {
  playBtn.addEventListener('click', () => playing ? pause() : play());
}
if (prevBtn) prevBtn.addEventListener('click', () => { if (!currentKey) return; currentTrack = (currentTrack - 1 + playlists[currentKey].tracks.length) % playlists[currentKey].tracks.length; trackMeta.textContent = playlists[currentKey].tracks[currentTrack]; renderPlaylistList(currentKey); });
if (nextBtn) nextBtn.addEventListener('click', () => { if (!currentKey) return; currentTrack = (currentTrack + 1) % playlists[currentKey].tracks.length; trackMeta.textContent = playlists[currentKey].tracks[currentTrack]; renderPlaylistList(currentKey); });

document.querySelectorAll('.radio-tags button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.radio-tags button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    load(btn.dataset.playlist);
    if (!playing) play();
  });
});

/* ============ MODAL DEMO ============ */
const uploadBtn = document.getElementById('uploadDemo');
const dialog = document.getElementById('demoDialog');
const closeBtn = document.getElementById('closeDialog');
const sendBtn = document.getElementById('sendDemo');
const dialogMsg = document.getElementById('dialogMessage');

if (uploadBtn) uploadBtn.addEventListener('click', () => dialog.showModal());
if (closeBtn) closeBtn.addEventListener('click', () => dialog.close());
if (sendBtn) sendBtn.addEventListener('click', () => {
  dialogMsg.textContent = '✓ Recibido. En la versión real esto se envía al servidor para moderación.';
  setTimeout(() => dialog.close(), 1500);
});