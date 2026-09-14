const buttons = document.querySelectorAll(".connect");
const select = document.querySelector("select");

if (select) {
    select.addEventListener("change", () => {
        buttons.forEach(button => {
            button.disabled = false;
        });
    });
}

if (buttons) {
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            saveSourceAndConnect();
        });
    });
}

function saveSourceAndConnect() {
    const selectedVal = select ? select.value : "Spotify";
    fetch("/save-source", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ source: selectedVal })
    })
    .then(() => {
        window.location.href = `/auth/start?platform=${encodeURIComponent(selectedVal)}`;
    })
    .catch(() => {
        window.location.href = `/auth/start?platform=${encodeURIComponent(selectedVal)}`;
    });
}
