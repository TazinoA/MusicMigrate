const buttons = document.querySelectorAll(".connect");
const select = document.querySelector("select");


select.addEventListener("change", () => {
    buttons.forEach(button=>{
        button.disabled = false;
    })
})


buttons.forEach(button => {
  button.addEventListener("click",() =>{
    window.location.href = "/"
  })
});