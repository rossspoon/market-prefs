$(window).on('load', function () {
    //Set content size to document size.
    let size_window = function() {
        let wh = $(window).height();
        let ratio = .7
        $('.elic-card').css('height', wh * ratio);
        $('.elic-card').css('width', wh * ratio);
    };
    size_window();
    $(window).resize(size_window);

    Chart.register(ChartDataLabels);
    //I don't want to interact with individual elements to register a custom mode that
    // returns no elements.
    Chart.Interaction.modes.none = function(chart, e, options, useFinalPosition) {
        return [];
    }

    let ctx_safe = document.getElementById('safe_card').getContext('2d');
    let safe_pie = make_chart(ctx_safe, js_vars.pct, js_vars.safe_pay);
    CHARTS.push(safe_pie);
    let ctx_risk = document.getElementById('risk_card').getContext('2d');
    let risk_pie = make_chart(ctx_risk, js_vars.pct, js_vars.risk_pay);
    CHARTS.push(risk_pie);
    
    
        
    //Add practice page background
    if (js_vars.is_practice) {
        console.log("PRACTICE")
        $('.otree-body').addClass('practice-bg');
        $('._otree-content, .otree-title').css('background-color', '#fafaff')
    }

});

CHARTS = []

function set_border(chart, color, clicked) {
    chart.data.datasets[0].borderColor = color;
    if (clicked) {
        chart.canvas.classList.add("clicked")
    } else {
        chart.canvas.classList.remove("clicked");
    }
}
function set_borders(color) {
    CHARTS.forEach((chart) => set_border(chart, color));
}
function update_charts() {
    CHARTS.forEach((chart) => chart.update());
}

function make_chart(ctx, pct, pay){
    const data = {
        labels: pay,
        datasets: [{
            data: pct,
            backgroundColor: [
                'rgb(255, 99, 132)',
                'rgb(54, 162, 235)',
            ],
            borderColor: 'white',
            borderWidth: 14,
        }]
    };

    const label_plug = {
        datalabels: {
            formatter: (value, ctx) => {
                let datasets = ctx.chart.data.datasets;

                let sum = 0;
                datasets.map(dataset => {
                    sum += dataset.data.reduce((partialSum, a) => partialSum + a, 0);
                });
                let lab = ctx.chart.data.labels[ctx.dataIndex];
                let percentage = Math.round((value / sum) * 100) + '%';
                return lab + '\n' + percentage;
            },
            color: '#fff',
            font:{size: 30}
        }
    };

    const other_plug = {
        legend: {display: false},
        tooltip: {enabled: false},
    }

    const opt_plugs = Object.assign({}, label_plug, other_plug);

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: opt_plugs,
        //events: ['click', 'touchstart'],
        onClick: (e, elems, chart) =>
        {
            set_borders('white', false);
            set_border(chart, 'yellow', true);
            update_charts();

            //Set hidden field
            const rfield = $("#risk")
            if (chart.canvas.getAttribute('id') == 'risk_card'){
                rfield.val(1)
            } else {
                rfield.val(0)
            }        },
        onHover: (e, elems, chart) =>
        {
            let canvas = chart.canvas;

            if (elems.length == 0) {
                canvas.classList.remove('o100');
                canvas.classList.add('o70');
            } else {
                canvas.classList.remove('o70');
                canvas.classList.add('o100');
            }
        },
        interaction: {mode: 'dataset'},
        animation: {duration: 0}
    };

   return  new Chart(ctx, {type: 'pie', data:data, options:options})
}

