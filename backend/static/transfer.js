const buttons = document.querySelectorAll(".connect");
const select = document.querySelector("select");


select.addEventListener("change", () => {
    buttons.forEach(button=>{
        button.disabled = false;
    })
})


buttons.forEach(button => {
  button.addEventListener("click",() =>{
    saveSource();
    window.location.href = `/auth/start?platform=${select.value}`
  })
});

function saveSource(){
  fetch("http://127.0.0.1:8000/save-source", {
    method:"POST",
     headers: {
        "Content-Type": "application/json"
      },
    body: JSON.stringify({source:select.value})
  })
}