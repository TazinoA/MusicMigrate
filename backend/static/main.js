const sourceSelect = document.querySelector("select");
const destinationSelect = document.querySelectorAll("select")[1];
const selectAllButton = document.querySelector("#select-all");
const checkboxes = document.querySelectorAll(".playlist input[type='checkbox']");
const transferButton = document.querySelector("#transfer-button");
const loadingOverlay = document.querySelector('.loading-overlay');
const backdrop = document.querySelector(".backdrop");
const searchBar = document.querySelector(".search-bar");
const playlists = document.querySelectorAll(".playlist");

const authModal = document.getElementById("authModal");
const authFrame = document.getElementById("authFrame");

function updateCountsAndButton() {
    const checked = document.querySelectorAll(".playlist input[type='checkbox']:checked");
    let songCount = 0;
    checked.forEach(cb => {
        songCount += parseInt(cb.value) || 0;
    });

    const playlistCountElem = document.querySelector("#playlist-count");
    if (playlistCountElem) playlistCountElem.textContent = checked.length;

    const trackCountElem = document.querySelector("#track-count");
    if (trackCountElem) trackCountElem.textContent = songCount;

    if (transferButton) {
        transferButton.disabled = checked.length === 0;
    }
}

if (checkboxes.length > 0) {
    checkboxes.forEach(cb => {
        cb.addEventListener("change", updateCountsAndButton);
    });
}

updateCountsAndButton();

if (searchBar) {
    searchBar.addEventListener("input", (e) => {
        const value = e.target.value.toLowerCase();
        playlists.forEach(playlist => {
            const isVisible = playlist.id.toLowerCase().includes(value);
            playlist.classList.toggle("hidden", !isVisible);
        });
    });
}

if (selectAllButton) {
    selectAllButton.addEventListener("click", () => {
        const allSelected = Array.from(checkboxes).every(cb => cb.checked);
        checkboxes.forEach(cb => {
            cb.checked = !allSelected;
        });
        updateCountsAndButton();
    });
}

if (sourceSelect) {
    sourceSelect.addEventListener("change", function () {
        const selectedValue = this.value;
        let currentSource = document.querySelector("#current-source");
        if (currentSource) currentSource.innerHTML = `from ${selectedValue}`;

        fetch("/save-source", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source: selectedValue })
        })
        .then(() => fetch(`/check-auth-status?platform=${encodeURIComponent(selectedValue)}`))
        .then(response => response.json())
        .then(data => {
            if (!data.is_authenticated) {
                window.location.href = `/transfer?platform=${encodeURIComponent(selectedValue)}`;
            }
        })
        .catch(error => {
            console.error("Error checking auth status for source platform:", error);
        });
    });
}

if (destinationSelect) {
    destinationSelect.addEventListener("change", function () {
        const selectedValue = this.value;

        fetch("/save-destination", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ destination: selectedValue })
        })
        .then(() => fetch(`/check-auth-status?platform=${encodeURIComponent(selectedValue)}`))
        .then(response => response.json())
        .then(data => {
            if (!data.is_authenticated) {
                window.location.href = `/auth/start?platform=${encodeURIComponent(selectedValue)}`;
            }
        })
        .catch(error => {
            console.error("Error checking auth status for destination platform:", error);
        });
    });
}

if (transferButton) {
    transferButton.addEventListener("click", handleSubmit);
}

function handleSubmit() {
    const checked = document.querySelectorAll(".playlist input[type='checkbox']:checked");
    if (checked.length === 0) {
        alert("Please select at least one playlist to transfer.");
        return;
    }

    const selectedPlaylists = [];
    checked.forEach(cb => {
        selectedPlaylists.push([cb.dataset.id, cb.name]);
    });

    showLoadingOverlay();

    const eventSource = new EventSource("/progress-stream");

    eventSource.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            if (data.complete) {
                eventSource.close();
                return;
            }
            if (data.ping) return;

            if (data.playlist) {
                const currPl = document.querySelector(".current-playlist");
                if (currPl) currPl.textContent = `Transferring: ${data.playlist}`;
            }

            if (data.total > 0 && data.currCount !== undefined) {
                const percentage = Math.floor((data.currCount / data.total) * 100);
                const pPct = document.querySelector(".progress-percentage");
                if (pPct) pPct.textContent = `${percentage}%`;

                const pFill = document.querySelector(".progress-fill");
                if (pFill) pFill.style.width = `${percentage}%`;
            }

            const statValues = document.querySelectorAll(".stat-value");
            if (statValues.length >= 2) {
                statValues[0].textContent = `${data.currPlaylist}/${data.totalPlaylists}`;
                statValues[1].textContent = `${data.currCount}/${data.totalSongs}`;
            }
        } catch (e) {
            console.error("Error parsing progress stream:", e);
        }
    };

    fetch("/get-playlists", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ playlists: selectedPlaylists })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Transfer failed"); });
        }
        return response.json();
    })
    .then(data => {
        eventSource.close();
        if (data.redirect) {
            window.location.href = data.redirect;
        }
    })
    .catch(error => {
        eventSource.close();
        hideLoadingOverlay();
        alert(`Transfer error: ${error.message}`);
    });
}

function showLoadingOverlay() {
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    if (backdrop) backdrop.style.display = "block";
}

function hideLoadingOverlay() {
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    if (backdrop) backdrop.style.display = "none";
}
