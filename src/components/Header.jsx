import React from "react";
import logo from "../images/logo.svg"
function Header(){
    return <div>
        <header className = "header">
            <div className = "header-left-section">
                {/* <img className = "logo" src = {logo}/> */}
            <h2>MusicMigrate</h2>
            </div>
            <div className = "header-right-section">
                <p>Features</p>
                <p>How it Works</p>
                <button>Get Started</button>
            </div>
        </header>
    </div>
}

export default Header;