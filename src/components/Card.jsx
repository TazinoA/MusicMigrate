import React from "react";


function Card(props){

    function handleClick(){
       window.location.href = "http://127.0.0.1:8000"
    }

    return <div className = "card">
        <button onClick = {handleClick}>
            <img src = {props.logo} alt = {props.name}></img>
            </button>
        </div>
}

export default Card;