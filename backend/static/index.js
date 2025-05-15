import axios from "axios"

let playlists = document.querySelectorAll(".playlist");
let selected = {};
function handleClick(playlist){
    if(playlist.id in selected){
        delete selected[playlist.id];
        playlist.classList.remove("selected");
    }else{
        selected[playlist.id] = playlist.name;
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