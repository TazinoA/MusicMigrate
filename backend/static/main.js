import axios from "https://esm.sh/axios"

const select = document.querySelector("select");
const buttons = document.querySelectorAll(".connect");
const selectAllButton = document.querySelector("#select-all");
const checkboxes = document.querySelectorAll(".playlist input[type='checkbox']");
const transferButton = document.querySelector("#transfer-button");
const source = new EventSource("/progress-stream");
const loadingOverlay = document.querySelector('.loading-overlay');
const backdrop = document.querySelector(".backdrop");

transferButton.addEventListener("click", handleSubmit);

checkboxes.forEach(cb => {
    cb.addEventListener("change",updateCounts)
})

selectAllButton.addEventListener("click", ()=> {
    const allSelected = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb =>{
        cb.checked = !allSelected;
        updateCounts();
    });
})

select.addEventListener("change", () => {
    const selectedValue = select.value;
    let currentSource = document.querySelector("#current-source")
    currentSource.innerHTML = `from ${selectedValue}`

    buttons.forEach(button=>{
        button.disabled = false;
    })
})

buttons.forEach(button => {
    button.addEventListener("click", handleClick);
})

function handleClick(){
    document.querySelector(".pre-connect").classList.add("hidden");
    document.querySelector(".pre-connect").style.order = 25;
    document.querySelector(".transfer-details").classList.remove("hidden");
    document.querySelector(".transfer-details").style.order = 3;
    document.querySelector(".display-playlists").classList.remove("hidden");
    document.querySelector(".display-playlists").style.order = 2;
    document.querySelector(".select-destination").classList.remove("hidden");
    document.querySelector(".select-platforms>button").classList.add("hidden");
}

function updateCounts() {
  const checked = document.querySelectorAll(".playlist input[type='checkbox']:checked");
  let songCount = 0;
  checked.forEach(cb => {
    songCount += parseInt(cb.value);
  });

  document.querySelector("#playlist-count").textContent = checked.length;
  document.querySelector("#track-count").textContent = songCount;
}


function handleSubmit(){
    const playlists = [];
    const checked = document.querySelectorAll(".playlist input[type='checkbox']:checked");

    checked.forEach(cb => {
        playlists.push([cb.dataset.id, cb.name])
    })

    axios.post("http://127.0.0.1:8000/get-playlists",
            {
                playlists:playlists
            }
        ).then(response => {
          console.log(response.status)
        }).finally(hideLoadingOverlay)
        showLoadingOverlay();
}

function showLoadingOverlay() {
  loadingOverlay.style.display = 'flex';
  backdrop.style.display = "block"; 
}

function hideLoadingOverlay() {
  loadingOverlay.style.display = 'none';
  backdrop.style.display = "none"
}

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