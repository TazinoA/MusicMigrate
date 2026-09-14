const transferBtn = document.querySelector(".transfer-button");
if (transferBtn) {
    transferBtn.addEventListener("click", () => {
        window.location.href = "/transfer";
    });
}

const headerBtn = document.querySelector(".header button");
if (headerBtn) {
    headerBtn.addEventListener("click", () => {
        window.location.href = "/transfer";
    });
}

const hiwBtn = document.querySelector("#hiw");
if (hiwBtn) {
    hiwBtn.addEventListener("click", () => {
        document.querySelector(".how-it-works")?.scrollIntoView({ behavior: "smooth" });
    });
}

const learnMoreBtn = document.querySelector(".learn-more");
if (learnMoreBtn) {
    learnMoreBtn.addEventListener("click", () => {
        document.querySelector(".how-it-works")?.scrollIntoView({ behavior: "smooth" });
    });
}
