document.querySelector(".transfer-button").addEventListener("click", () => {
    window.location.href = "http://127.0.0.1:8000/transfer";
})

document.querySelector(".header button").addEventListener("click", () => {
    window.location.href = "http://127.0.0.1:8000/transfer";
})

document.querySelector("#hiw").addEventListener("click" ,() =>{
    document.querySelector(".how-it-works").scrollIntoView({behavior:"smooth"});
});