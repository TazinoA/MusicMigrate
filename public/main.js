let cards = document.querySelectorAll(".card");

cards.forEach(card => {
    card.addEventListener("click", () => {
        window.location.href = "http://127.0.0.1:8000"
    })
});