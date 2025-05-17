import React from "react";
import Card from "./components/Card";
import Header from "./components/Header"
import cards from "./card"
function App(){

    function createCard(card){
        return <Card key = {card.name} logo = {card.src} name = {card.name}/>
    }

    return <div class = "app">
        <Header />
       <main className = "content">
         <div className = "title">
            <h1>Select The Source</h1>
         </div>
        <div className = "card-container">
            {cards.map(card => createCard(card))}
        </div>
       </main>
    </div>
}


export default App;