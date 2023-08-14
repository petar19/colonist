function main() {
    const chat = document.getElementById("game-log-text")
    const messages = chat.innerHTML;
    let sendToDiscord = true
    if (!confirm("Send to Discord?")) sendToDiscord = false
    const reqBody = {messages, sendToDiscord};

    
    let url2 = "http://localhost:5009/analizeGame"
    fetch(url2, {method: "POST", body:JSON.stringify(reqBody)})
}
main()