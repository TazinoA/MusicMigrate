import axios from "https://esm.sh/axios"

const sourceSelect = document.querySelector("select");
const destinationSelect = document.querySelectorAll("select")[1];
const selectAllButton = document.querySelector("#select-all");
const checkboxes = document.querySelectorAll(".playlist input[type='checkbox']");
const transferButton = document.querySelector("#transfer-button");
const source = new EventSource("/progress-stream");
const loadingOverlay = document.querySelector('.loading-overlay');
const backdrop = document.querySelector(".backdrop");
const searchBar = document.querySelector(".search-bar");
const playlists = document.querySelectorAll(".playlist");

const authModal = document.getElementById("authModal");
const authFrame = document.getElementById("authFrame");
const modalCloseButton = document.querySelector(".modal-close-button"); 

transferButton.addEventListener("click", handleSubmit);

checkboxes.forEach(cb => {
    cb.addEventListener("change",updateCounts)
})

searchBar.addEventListener("input" ,(e) => {
 const value = e.target.value.toLowerCase();
 playlists.forEach(playlist =>{
 const isVisible = playlist.id.toLowerCase().includes(value);
 playlist.classList.toggle("hidden", !isVisible);
 })
});

selectAllButton.addEventListener("click", ()=> {
    const allSelected = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb =>{
        cb.checked = !allSelected;
        updateCounts();
    });
})

sourceSelect.addEventListener("change", function () {
  const selectedValue = this.value;
  let currentSource = document.querySelector("#current-source")
  currentSource.innerHTML = `from ${selectedValue}`;

  axios.get(`/check-auth-status?platform=${selectedValue}`)
    .then(response => {
      const { is_authenticated } = response.data;
      if (!is_authenticated) {
        window.location.href = `/transfer?platform=${selectedValue}`;
      }
    })
    .catch(error => {
      console.error("Error checking auth status for source platform:", error);
    });
});

destinationSelect.addEventListener("change", function () {
  const selectedValue = this.value;

  axios.get(`/check-auth-status?platform=${selectedValue}`)
    .then(response => {
      const { is_authenticated } = response.data;
      if (!is_authenticated) {
        openAuthModal(selectedValue);
        axios.get( `/auth/start?platform=${selectedValue}`)
      }
    })
    .catch(error => {
      console.error("Error checking auth status for destination platform:", error);
    });
});


async function openAuthModal(platformName) {
    if (authModal && authFrame) {
        const response = await fetch(`/auth/start?platform=${platformName}`);
        const data = await response.json();
        const authUrl = data.auth_url;

        window.location.href = authUrl;
        // authModal.style.display = "flex";
    }
}
function closeAuthModal() {
    if (authModal) {
        authModal.style.display = "none";
    }
    if (authFrame) {
        authFrame.src = "";
    }
}

window.closeAuthModal = closeAuthModal;



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
          window.location.href = response.data.redirect;
        }).catch(error =>{
          console.error(error);
        }).finally(hideLoadingOverlay);


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