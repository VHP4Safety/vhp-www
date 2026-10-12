// Archive timeline: groups the date-stamped cards by year and adds a sticky year bar on the left.
// Without JavaScript the page is still the plain list of cards.
(function () {
  var nav = document.querySelector(".timeline");
  var cards = document.querySelectorAll(".timeline-content .card[data-date]");
  if (!nav || !cards.length) return;

  var groups = {}, order = [];
  cards.forEach(function (card) {
    var year = card.dataset.date.slice(0, 4);
    if (!groups[year]) { groups[year] = []; order.push(year); }
    groups[year].push(card);
  });

  var links = {}, sections = [];
  order.forEach(function (year) {
    var grid = document.createElement("div");
    grid.className = "cards";
    var heading = document.createElement("h2");
    heading.className = "timeline-year";
    heading.id = "y" + year;
    heading.textContent = year;
    groups[year][0].parentNode.before(heading, grid);
    groups[year].forEach(function (card) { grid.appendChild(card); });
    sections.push(heading);

    var a = document.createElement("a");
    a.href = "#y" + year;
    a.innerHTML = "<span>" + year + "</span><small>" + groups[year].length + "</small>";
    nav.appendChild(a);
    links[year] = a;
  });
  // the original (now empty) grid is no longer needed
  document.querySelectorAll(".timeline-content > .cards:empty").forEach(function (e) { e.remove(); });

  function update() {
    var current = order[0];
    sections.forEach(function (h) { if (h.getBoundingClientRect().top < window.innerHeight * 0.35) current = h.textContent; });
    order.forEach(function (y) { links[y].classList.toggle("active", y === current); });
  }
  window.addEventListener("scroll", update, { passive: true });
  update();
})();
