import axios from "https://esm.sh/axios"

let playlists = document.querySelectorAll(".playlist");
let selected = new Map();

function handleClick(playlist){
    const name = playlist.getAttribute("name");
    const id = playlist.id;

    if(selected.has(id)){
        selected.delete(id);
        playlist.classList.remove("selected");
    }else{
        selected.set(id, [id, name]);
        playlist.classList.add("selected");
    }
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
    axios.post("http://127.0.0.1:8000/get-playlists",
        {
            playlists: Array.from(selected.values()),
        }
    )
}

document.querySelector("button").addEventListener("click", handleSubmit)