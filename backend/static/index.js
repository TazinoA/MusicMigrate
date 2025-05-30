import axios from "https://esm.sh/axios"

let playlists = document.querySelectorAll(".playlist");
let selected = new Map();
const loadingOverlay = document.querySelector('.loading-overlay');
document.querySelector(".choose-destination").addEventListener("click", handleSubmit);

document.querySelector(".select-all").addEventListener("click",async() => {
 for(const playlist of playlists){
  playlist.click();
  await sleep(10);
 }
})

function sleep(ms){return new Promise(resolve => setTimeout(resolve, ms));}



playlists.forEach(playlist => {
    playlist.addEventListener("click",() => {
        handleClick(playlist)
    })
})

function showLoadingOverlay() {
  loadingOverlay.style.display = 'flex'; 
}

function hideLoadingOverlay() {
  loadingOverlay.style.display = 'none';
}

function handleClick(playlist){
    const name = playlist.getAttribute("name");
    const id = playlist.id;
    const count = playlist.getAttribute("count")

    if(selected.has(id)){
        selected.delete(id);
        playlist.classList.remove("selected");
    }else{
        selected.set(id, [id, name, count]);
        playlist.classList.add("selected");
    }

    const selectedObj = Array.from(selected.values()).map(([id, name, count]) => ({
  id,
  name,
  count,
}));

    fetch('/update-selected', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selectedPlaylists: selectedObj })
  })
  .then(res => res.text())
  .then(html => {
    document.getElementById('section').innerHTML = html;
  });

}

function handleSubmit(){
    if(selected.size === 0){
        return
    }
    const playlistsToSend = Array.from(selected.values()).map(([id, name]) => [id, name]);
    axios.post("http://127.0.0.1:8000/get-playlists",
        {
            playlists:playlistsToSend
        }
    ).then(response => {
      console.log(response.status)
    }).finally(hideLoadingOverlay)
    showLoadingOverlay();
}


const source = new EventSource("/progress-stream");

  source.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    
    document.querySelector(".loading-overlay").style.display = "flex";

    
    document.querySelector(".current-playlist").textContent = `Transferring: ${data.playlist}`;

    
    const percentage = Math.floor((data.currCount / data.total) * 100);
    document.querySelector(".progress-percentage").textContent = `${percentage}%`;

    
    document.querySelector(".progress-fill").style.width = `${percentage}%`;

    
    document.querySelectorAll(".stat-value")[0].textContent = `${data.currPlaylist}/${data.totalPlaylists}`;
    document.querySelectorAll(".stat-value")[1].textContent = `${data.currCount}/${data.totalSongs}`;
  };