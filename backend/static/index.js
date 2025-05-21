import axios from "https://esm.sh/axios"

let playlists = document.querySelectorAll(".playlist");
let selected = new Map();
document.querySelector(".transfer-button").addEventListener("click", handleSubmit)

const loadingOverlay = document.querySelector('.loading-overlay');

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

playlists.forEach(playlist => {
    playlist.addEventListener("click",() => {
        handleClick(playlist)
    })
})

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
