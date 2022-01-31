$(window).on('load', function () {
  const canvas = document.getElementById("market_screen")
  const context = canvas.getContext("2d")
  const img = new Image()
  img.src = "/static/instructions/img/market_01.png"
  img.onload = () => {
    context.drawImage(img, 0, 0, canvas.width, canvas.height)
  }
});

