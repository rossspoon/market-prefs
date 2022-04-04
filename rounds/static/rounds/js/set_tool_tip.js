function set_tool_tips(){
    let elem;
    let text_span;
    for (const [elem_id, data] of Object.entries(js_vars.tt)) {
        elem = document.getElementById(elem_id)
        if (!elem){
            continue;
        }
        elem.classList.add('tool-tip');

        text_span = document.createElement('span');
        text_span.classList.add('tool-tip-text', data.pos_cls);
        text_span.innerHTML = data.text;
        elem.append(text_span)
    }
};