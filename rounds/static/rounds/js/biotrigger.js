
async function sendPageEvent(websocket) {
    const event = {
        mtype: js_vars.event_type,
        page_name: js_vars.page_name,
        round_num: js_vars.rnd,
        p_label: js_vars.label,
        participant: js_vars.part_code,
        is_practice: js_vars.is_practice,
    }

    websocket.send(JSON.stringify(event))
}

function send_events(websocket){
    $("#shutdown_button").on('click', function(){
        const event = {
            mtype: 'stop_exp',
            round_num: '-99',
        }
        websocket.send(JSON.stringify(event))
    });
}

window.addEventListener("DOMContentLoaded", () => {
    const websocket = new WebSocket("ws://localhost:8345")
    websocket.onopen = () => sendPageEvent(websocket)
    send_events(websocket);
});