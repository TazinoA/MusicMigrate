const platforms = document.querySelectorAll(".platform");

platforms.forEach(platform => {
    platform.addEventListener("click", () => {
        platform.classList.toggle("selected");
    })
})