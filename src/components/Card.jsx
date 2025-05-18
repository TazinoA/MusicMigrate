import React from "react";


function Card(props){

    function handleClick(){
       //window.location.href = "http://127.0.0.1:8000"
    }

    return <div className = "card" onClick = {handleClick}>
            <img src = {props.logo} alt = {props.name} style = {props.style}></img>
            <p>{props.name}</p>
        </div>
}

export default Card;