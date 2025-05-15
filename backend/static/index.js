let playlists = document.querySelectorAll(".playlist");
let selected = new Set();
function handleClick(playlist){
    if(selected.has(playlist.id)){
        selected.delete(playlist.id);
        playlist.classList.remove("selected");
    }else{
        selected.add(playlist.id);
        playlist.classList.add("selected");
    }
}

playlists.forEach(playlist => {
    playlist.addEventListener("click",() => {
        handleClick(playlist)
    })
})