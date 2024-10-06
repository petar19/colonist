function main() {
    // const chatXpath = '//*[@id="game-log-text"]'
    // const chat = $x(chatXpath)[1]
    let chat = document.getElementById("game-log-text")
    if (chat.innerHTML === '') {
        chat.remove()
        chat = document.getElementById("game-log-text")
    }
    
    const messages = chat.innerHTML;
    let sendToDiscord = true
    if (!confirm("Send to Discord?")) sendToDiscord = false
    const reqBody = {messages, sendToDiscord};
    console.log(reqBody)
    
    let url2 = "http://localhost:5009/analizeGame"
    fetch(url2, {method: "POST", body:JSON.stringify(reqBody)})
}
main()