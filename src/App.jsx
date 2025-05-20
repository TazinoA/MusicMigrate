import React from "react";
import Card from "./components/Card";
import Header from "./components/Header"
import cards from "./cards"
import spotifylogo from "./images/spotify.svg"
import applelogo from "./images/apple-music.svg"
import deezerlogo from "./images/deezer.svg"
import youtubelogo from "./images/youtube.svg"
import amazonlogo from "./images/amazon.svg"
import hero from "./images/hero.svg"

const logos = [spotifylogo, applelogo ,youtubelogo, amazonlogo, deezerlogo]

function App(){

    function createCard(card, i){
        return <Card key = {card.name} logo = {logos[i]} name = {card.name} style = {{...card.color, ...card.textColor}}/>
    }

    return <div className = "app">
        <Header />
       <main className = "content">
         <div className = "title">
            <div className = "title-left-section">
                <h1>Transfer Your Music Playlists Between Platforms</h1>
                <p>Easily move your playlists between Spotify, Apple Music, YouTube Music, and more with just a few clicks.</p>
                <button>Start Transferring →</button>
            </div>
           <div className = "title-right-section"> <img src = {hero}></img></div>
         </div>
         <div className = "platform-title">
            <h2>Supported Platforms</h2>
            <p>Transfer your playlists between major music streaming services</p>
         </div>
        <div className = "card-container">
            {cards.map((card, i) => createCard(card, i))}
        </div>
       </main>
    </div>
}


export default App;