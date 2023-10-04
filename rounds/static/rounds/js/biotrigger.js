
async function sendPageName(websocket) {
    const event = {
        type: "page_start",
        page_name: js_vars.page_name,
        round: js_vars.rnd,
        label: js_vars.label,
    }

    websocket.send(JSON.stringify(event))
}

window.addEventListener("DOMContentLoaded", () => {
    const websocket = new WebSocket("ws://localhost:8345")
    websocket.onopen = () => sendPageName(websocket)
});