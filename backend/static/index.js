import axios from "axios"

let playlists = document.querySelectorAll(".playlist");
let selected = new Set();
function handleClick(playlist){
    if(selected.has([playlist.id, playlist.name])){
        selected.remove(playlist.id, playlist.name);
        playlist.classList.remove("selected");
    }else{
        selected.add(playlist.id, playlist.name);
        playlist.classList.add("selected");
    }
}

playlists.forEach(playlist => {
    playlist.addEventListener("click",() => {
        handleClick(playlist)
    })
})

function handleSubmit(){
    axios.post("http://127.0.0.1:8000/get-playlists",
        {
            playlists: selected,
        }
    )
}

document.querySelector("button").addEventListener("click", handleSubmit)