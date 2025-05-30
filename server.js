import express from "express"
import cards from "./cards.js"

const app = express();
app.set("view engine", "ejs")
app.use(express.static("public"))


app.get("/", (req, res) => {
    res.render("index", {cards})
})

app.get("/select-source", (req, res) => {
    const query = req.query;

    if(query !==null){
        const filtered = cards.filter((card) => card.name !== query.source);
        res.render("source", {cards:filtered})
    }else{
        res.render("source", {cards})
    }
})

app.get("/transfer", (req, res) => {
    res.render("transfer", {cards})
})


app.listen(3000, () => {
    console.log("running on http://localhost:3000")
})
