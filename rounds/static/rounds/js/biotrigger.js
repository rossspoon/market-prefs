
async function sendPageEvent(websocket) {
    const event = {
        type: js_vars.event_type,
        page_name: js_vars.page_name,
        round_num: js_vars.rnd,
        p_label: js_vars.label,
        participant: js_vars.part_code,
    }

    websocket.send(JSON.stringify(event))
}

function send_events(websocket){
    $("#shutdown_button").onclick(function(){
        const event = {
            type: 'stop_exp',
            round: 'x',
        }
        websocket.send(JSON.stringify(event))
    });
}

window.addEventListener("DOMContentLoaded", () => {
    const websocket = new WebSocket("ws://localhost:8345")
    websocket.onopen = () => sendPageEvent(websocket)
    send_events(websocket);
});