const select = document.querySelector("select");
const buttons = document.querySelectorAll("button");

select.addEventListener("change", () => {
    const selectedValue = select.value;
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