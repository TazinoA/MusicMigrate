import React from "react";


function Card(props){

    function handleClick(){
       window.location.href = "http://127.0.0.1:8000"
    }

    return <div className = "card">
        <img src = {props.logo} alt = {props.name} onClick = {handleClick}></img>
        </div>
}

export default Card;