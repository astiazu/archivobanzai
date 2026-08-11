const playlists = {
  "70s": [
    ["70s / DISCO", "Archivo pendiente de selección"],
    ["70s / FUNK", "Archivo pendiente de selección"],
    ["70s / ROCK", "Archivo pendiente de selección"]
  ],
  "80s": [
    ["80s / POP", "Archivo pendiente de selección"],
    ["80s / NEW WAVE", "Archivo pendiente de selección"],
    ["80s / ROCK NACIONAL", "Archivo pendiente de selección"]
  ],
  "90s": [
    ["90s / DANCE", "Archivo pendiente de selección"],
    ["90s / EURODANCE", "Archivo pendiente de selección"],
    ["90s / POP & ROCK", "Archivo pendiente de selección"]
  ],
  "2000s": [
    ["2000s / DANCE", "Archivo pendiente de selección"],
    ["2000s / POP", "Archivo pendiente de selección"],
    ["2000s / ELECTRÓNICA", "Archivo pendiente de selección"]
  ],
  rock: [
    ["ROCK / CLÁSICOS", "Archivo pendiente de selección"],
    ["ROCK / NACIONAL", "Archivo pendiente de selección"],
    ["ROCK / ALTERNATIVO", "Archivo pendiente de selección"]
  ],
  dance: [
    ["DANCE / CLASSICS", "Archivo pendiente de selección"],
    ["DANCE / HOUSE", "Archivo pendiente de selección"],
    ["DANCE / EURO", "Archivo pendiente de selección"]
  ],
  latino: [
    ["LATINOS / CLÁSICOS", "Archivo pendiente de selección"],
    ["LATINOS / 90s", "Archivo pendiente de selección"],
    ["LATINOS / FIESTA", "Archivo pendiente de selección"]
  ],
  banzai: [
    ["BANZAI / VERANO 1989", "Playlist a reconstruir"],
    ["BANZAI / VERANO 1993", "Playlist a reconstruir"],
    ["BANZAI / VERANO 1997", "Playlist a reconstruir"]
  ]
};

let currentList = [];
let currentIndex = 0;
let playing = false;
let timer = null;
let progress = 0;

const playlistList = document.querySelector("#playlistList");
const title = document.querySelector("#trackTitle");
const meta = document.querySelector("#trackMeta");
const nowPlaying = document.querySelector("#nowPlaying");
const progressBar = document.querySelector("#progress");
const playBtn = document.querySelector("#playBtn");
const player = document.querySelector(".radio-player");
const disc = document.querySelector(".disc");

function loadPlaylist(key){
  currentList = playlists[key] || playlists["90s"];
  currentIndex = 0;
  renderTracks();
  loadTrack(0);
  document.querySelectorAll(".radio-tags button").forEach(b => b.classList.toggle("active", b.dataset.playlist === key));
}
function renderTracks(){
  playlistList.innerHTML = currentList.map((item,i)=>`
    <div class="track ${i===currentIndex ? "active":""}" data-index="${i}">
      <small>${String(i+1).padStart(2,"0")}</small>
      <strong>${item[0]}</strong>
      <small>${item[1]}</small>
    </div>`).join("");
  playlistList.querySelectorAll(".track").forEach(el => el.addEventListener("click",()=>loadTrack(Number(el.dataset.index))));
}
function loadTrack(index){
  currentIndex = (index + currentList.length) % currentList.length;
  const [name, description] = currentList[currentIndex];
  title.textContent = name;
  meta.textContent = description;
  nowPlaying.textContent = name;
  progress = 0;
  progressBar.style.width = "0%";
  renderTracks();
}
function togglePlay(){
  playing = !playing;
  playBtn.textContent = playing ? "Ⅱ" : "▶";
  player.classList.toggle("playing", playing);
  if(playing){
    timer = setInterval(()=>{
      progress += 1;
      progressBar.style.width = progress + "%";
      if(progress >= 100){
        progress = 0;
        loadTrack(currentIndex + 1);
      }
    }, 120);
  }else{
    clearInterval(timer);
  }
}
document.querySelectorAll(".radio-tags button").forEach(btn=>{
  btn.addEventListener("click",()=>loadPlaylist(btn.dataset.playlist));
});
playBtn.addEventListener("click",togglePlay);
document.querySelector("#nextBtn").addEventListener("click",()=>loadTrack(currentIndex+1));
document.querySelector("#prevBtn").addEventListener("click",()=>loadTrack(currentIndex-1));
loadPlaylist("90s");

const dialog = document.querySelector("#demoDialog");
document.querySelector("#uploadDemo").addEventListener("click",()=>dialog.showModal());
document.querySelector("#closeDialog").addEventListener("click",()=>dialog.close());
document.querySelector("#sendDemo").addEventListener("click",()=>{
  document.querySelector("#dialogMessage").textContent = "Demo guardada visualmente. En la siguiente etapa conectamos este formulario al backend.";
});
