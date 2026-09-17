import express from "express"
import cards from "./cards.js"

const app = express();
app.set("view engine", "ejs")
app.use(express.static("public"))

const FLASK_URL = process.env.FLASK_URL || "http://127.0.0.1:8000";

app.get("/", (req, res) => {
    res.render("index", { cards })
})

app.get("/transfer", (req, res) => {
    res.redirect(`${FLASK_URL}/transfer`);
})

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`running on http://localhost:${PORT}`)
})
