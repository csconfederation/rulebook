const domains = [
    "https://csconfederation.com",
    "https://www.csconfederation.com",
    "http://localhost:3000"
  ]

window.addEventListener("message", messageHandler, false);function messageHandler(event) {
    currentColorScheme = JSON.parse(localStorage.getItem("/.__palette"))

    if (domains.includes(event.origin)){
        // Set an embedded class on body
        document.body.classList.add("embedded")

        if(event.data === "light" && currentColorScheme.index == 1){
            window.localStorage.setItem("/.__palette", '{"index":0,"color":{"scheme":"default","primary":"","accent":""}}')
            location.reload()
        }else if(event.data === "dark" && currentColorScheme.index == 0){
            window.localStorage.setItem("/.__palette", '{"index":1,"color":{"scheme":"slate","primary":"","accent":""}}')
            location.reload()
        }
    }
  }
