const searchBar = document.querySelector(".search-bar");
const songs = document.querySelectorAll(".song")
const selectPlaylists = document.querySelector("select")


selectPlaylists.addEventListener("change", () => {
    let currPlaylist = selectPlaylists.value;

    songs.forEach(song =>{
        const playlist = song.querySelector(".playlist-name")
        const isVisible = playlist.innerHTML === currPlaylist || currPlaylist === "all";
        song.classList.toggle("hidden", !isVisible);
    })
})


searchBar.addEventListener("input", (e) =>{
    const value = e.target.value.toLowerCase();

    songs.forEach(song =>{
        const isVisible = song.id.toLowerCase().includes(value);
        song.classList.toggle("hidden", !isVisible);
    })
})