/* Interactive MAC/MAB chart: realized abatement vs. Nash / cooperative optimum.
 * No build step and no external libraries - the chart is hand-rolled SVG. */
(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var WIDTH = 920;
  var HEIGHT = 540;
  var MARGIN = { top: 44, right: 24, bottom: 92, left: 74 };

  var els = {
    country: document.getElementById("country"),
    year: document.getElementById("year"),
    spec: document.getElementById("spec"),
    measure: document.getElementById("measure"),
    focus: document.getElementById("focus"),
    nash: document.getElementById("bm-nash"),
    coop: document.getElementById("bm-coop"),
    status: document.getElementById("status"),
    verdicts: document.getElementById("verdicts"),
    chart: document.getElementById("chart"),
    tooltip: document.getElementById("tooltip"),
    details: document.getElementById("details"),
    demoBanner: document.getElementById("demo-banner")
  };

  var meta = null;
  var requestToken = 0;

  // ---------------------------------------------------------------- helpers

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#888";
  }

  function svg(tag, attrs, text) {
    var node = document.createElementNS(SVG_NS, tag);
    for (var key in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, key) && attrs[key] !== null) {
        node.setAttribute(key, attrs[key]);
      }
    }
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function fmtPct(value) {
    if (value === null || value === undefined) return "n/a";
    return value.toFixed(Math.abs(value) < 10 ? 2 : 1) + "%";
  }

  function fmtMoney(value) {
    if (value === null || value === undefined) return "n/a";
    var abs = Math.abs(value);
    var digits = abs >= 100 ? 0 : abs >= 10 ? 1 : 2;
    return "$" + value.toFixed(digits);
  }

  function setStatus(message, isError) {
    if (!message) {
      els.status.classList.add("hidden");
      els.status.textContent = "";
      return;
    }
    els.status.textContent = message;
    els.status.classList.remove("hidden");
    els.status.classList.toggle("error", !!isError);
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function getJSON(url) {
    return fetch(url, { headers: { Accept: "application/json" } }).then(function (response) {
      return response.json().then(function (payload) {
        if (!response.ok) throw new Error(payload && payload.error ? payload.error : response.statusText);
        return payload;
      }, function () {
        throw new Error("Server returned " + response.status);
      });
    });
  }

  function selectedMeasures() {
    return els.measure.value.split(",");
  }

  function selectedBenchmarks() {
    var picked = [];
    if (els.nash.checked) picked.push("nash");
    if (els.coop.checked) picked.push("coop");
    return picked;
  }

  function query(extra) {
    var params = new URLSearchParams();
    params.set("year", els.year.value);
    params.set("spec", els.spec.value);
    params.set("measure", selectedMeasures().join(","));
    params.set("focus", els.focus.value);
    var benchmarks = selectedBenchmarks();
    if (benchmarks.length) params.set("benchmark", benchmarks.join(","));
    for (var key in extra) {
      if (Object.prototype.hasOwnProperty.call(extra, key)) params.set(key, extra[key]);
    }
    return params.toString();
  }

  var SERIES_COLORS = {
    nash: "--nash",
    coop: "--coop",
    den: "--den",
    strng: "--strng"
  };

  function colorFor(key) {
    return cssVar(SERIES_COLORS[key] || "--accent");
  }

  // ------------------------------------------------------------------ scales

  function linearScale(domain, range) {
    var d0 = domain[0], d1 = domain[1];
    var span = d1 - d0 || 1;
    return function (value) {
      return range[0] + ((value - d0) / span) * (range[1] - range[0]);
    };
  }

  /** Round "nice" tick values covering [lo, hi] with roughly `count` steps. */
  function ticks(lo, hi, count) {
    var span = hi - lo;
    if (!(span > 0)) return [lo];
    var rough = span / count;
    var magnitude = Math.pow(10, Math.floor(Math.log(rough) / Math.LN10));
    var candidates = [1, 2, 2.5, 5, 10];
    var step = magnitude * candidates[candidates.length - 1];
    for (var i = 0; i < candidates.length; i++) {
      if (magnitude * candidates[i] >= rough) { step = magnitude * candidates[i]; break; }
    }
    var out = [];
    for (var t = Math.ceil(lo / step) * step; t <= hi + step * 1e-9; t += step) {
      out.push(Math.abs(t) < step * 1e-9 ? 0 : t);
    }
    return out;
  }

  // ------------------------------------------------------------------- chart

  function drawChart(data) {
    clear(els.chart);
    els.tooltip.classList.add("hidden");

    var plotW = WIDTH - MARGIN.left - MARGIN.right;
    var plotH = HEIGHT - MARGIN.top - MARGIN.bottom;

    var xMin = data.x_range[0];
    var xMax = data.x_range[1];
    var yMin = data.y_range[0];
    var yMax = data.y_range[1];

    var x = linearScale([xMin, xMax], [0, plotW]);
    var y = linearScale([yMin, yMax], [plotH, 0]);

    var root = svg("svg", {
      viewBox: "0 0 " + WIDTH + " " + HEIGHT,
      role: "img",
      "aria-label": "Marginal abatement cost and benefit for " + data.country_name
    });

    root.appendChild(svg("text", {
      class: "chart-title", x: MARGIN.left, y: 24
    }, data.country_name + " — " + data.year + " — " + data.spec_label));

    var plot = svg("g", { transform: "translate(" + MARGIN.left + "," + MARGIN.top + ")" });
    root.appendChild(plot);

    // grid + axes ---------------------------------------------------------
    var grid = svg("g", { class: "grid" });
    var yTicks = ticks(yMin, yMax, 6);
    yTicks.forEach(function (value) {
      grid.appendChild(svg("line", { x1: 0, x2: plotW, y1: y(value), y2: y(value) }));
    });
    plot.appendChild(grid);

    var axes = svg("g", { class: "axis" });
    axes.appendChild(svg("line", { x1: 0, x2: plotW, y1: y(yMin), y2: y(yMin) }));
    axes.appendChild(svg("line", { x1: x(Math.max(xMin, 0)), x2: x(Math.max(xMin, 0)), y1: 0, y2: plotH }));

    ticks(xMin, xMax, 7).forEach(function (value) {
      if (value < xMin || value > xMax) return;
      axes.appendChild(svg("line", { x1: x(value), x2: x(value), y1: plotH, y2: plotH + 5 }));
      axes.appendChild(svg("text", {
        x: x(value), y: plotH + 18, "text-anchor": "middle"
      }, value.toFixed(Math.abs(xMax - xMin) < 5 ? 1 : 0)));
    });
    yTicks.forEach(function (value) {
      axes.appendChild(svg("text", {
        x: -8, y: y(value) + 4, "text-anchor": "end"
      }, Math.abs(value) >= 1000 ? (value / 1000).toFixed(1) + "k" : value.toFixed(0)));
    });
    plot.appendChild(axes);

    root.appendChild(svg("text", {
      class: "axis-title",
      x: MARGIN.left + plotW / 2,
      y: HEIGHT - MARGIN.bottom + 46,
      "text-anchor": "middle"
    }, "Abatement rate μ (% below baseline)"));

    root.appendChild(svg("text", {
      class: "axis-title",
      transform: "translate(18," + (MARGIN.top + plotH / 2) + ") rotate(-90)",
      "text-anchor": "middle"
    }, "Marginal cost / benefit ($ per tCO₂)"));

    var legend = [];

    // confidence bands for realized measures ------------------------------
    data.measures.forEach(function (measure) {
      if (measure.low === null || measure.high === null) return;
      var left = Math.max(xMin, Math.min(measure.low, measure.high));
      var right = Math.min(xMax, Math.max(measure.low, measure.high));
      if (!(right > left)) return;
      plot.appendChild(svg("rect", {
        class: "ci-band",
        x: x(left), y: 0,
        width: x(right) - x(left), height: plotH,
        fill: colorFor(measure.key)
      }));
    });

    // MAC curve ------------------------------------------------------------
    var path = data.curve.map(function (point, index) {
      return (index ? "L" : "M") + x(point.mu).toFixed(2) + "," + y(point.mac).toFixed(2);
    }).join(" ");
    plot.appendChild(svg("path", { class: "mac-curve", d: path }));
    legend.push({ label: "MAC curve", color: cssVar("--mac"), dash: null });

    // marginal benefit lines ----------------------------------------------
    data.benefit_lines.forEach(function (line) {
      var color = line.key === "nash" ? cssVar("--mab-local") : cssVar("--mab-global");
      if (!line.off_scale) {
        plot.appendChild(svg("line", {
          class: "mab-line",
          x1: 0, x2: plotW, y1: y(line.value), y2: y(line.value),
          stroke: color
        }));
      }
      legend.push({
        label: line.label + " = " + fmtMoney(line.value) + (line.off_scale ? " (off scale)" : ""),
        color: color,
        dash: null
      });
    });

    // vertical markers -----------------------------------------------------
    function marker(item, dash, labelPrefix) {
      var color = colorFor(item.key);
      if (!item.off_scale) {
        plot.appendChild(svg("line", {
          class: "marker-line",
          x1: x(item.mu), x2: x(item.mu), y1: 0, y2: plotH,
          stroke: color, "stroke-dasharray": dash
        }));
        var crossing = item.scc !== undefined && item.scc !== null ? item.scc : item.mac;
        if (crossing >= yMin && crossing <= yMax) {
          plot.appendChild(svg("circle", { cx: x(item.mu), cy: y(crossing), r: 4.5, fill: color }));
        }
      }
      legend.push({
        label: labelPrefix + ": μ = " + fmtPct(item.mu) + (item.off_scale ? " (off scale)" : ""),
        color: color,
        dash: dash
      });
    }

    data.benchmarks.forEach(function (item) {
      marker(item, item.key === "nash" ? "7 4" : "9 3 2 3", item.label);
    });
    data.measures.forEach(function (item) {
      marker(item, "2 3", "Realized — " + item.label);
    });

    // legend ---------------------------------------------------------------
    var legendGroup = svg("g", { class: "legend" });
    var lx = MARGIN.left;
    var ly = HEIGHT - MARGIN.bottom + 66;
    var perRow = 2;
    var colWidth = (WIDTH - MARGIN.left - MARGIN.right) / perRow;
    legend.forEach(function (item, index) {
      var col = index % perRow;
      var row = Math.floor(index / perRow);
      var ox = lx + col * colWidth;
      var oy = ly + row * 17;
      legendGroup.appendChild(svg("line", {
        x1: ox, x2: ox + 22, y1: oy - 4, y2: oy - 4,
        stroke: item.color, "stroke-width": 2.5, "stroke-dasharray": item.dash
      }));
      legendGroup.appendChild(svg("text", { x: ox + 28, y: oy }, item.label));
    });
    root.appendChild(legendGroup);

    // extend the SVG if the legend needs more rows than the margin allows
    var rows = Math.ceil(legend.length / perRow);
    var needed = ly + rows * 17 + 6;
    if (needed > HEIGHT) root.setAttribute("viewBox", "0 0 " + WIDTH + " " + needed);

    // hover crosshair ------------------------------------------------------
    var hover = svg("g", { opacity: 0 });
    var hoverLine = svg("line", { y1: 0, y2: plotH, stroke: cssVar("--muted"), "stroke-width": 1 });
    var hoverDot = svg("circle", { r: 3.5, fill: cssVar("--mac") });
    hover.appendChild(hoverLine);
    hover.appendChild(hoverDot);
    plot.appendChild(hover);

    var capture = svg("rect", {
      x: 0, y: 0, width: plotW, height: plotH, fill: "transparent"
    });
    plot.appendChild(capture);

    capture.addEventListener("mousemove", function (event) {
      var box = root.getBoundingClientRect();
      // .chart-wrap is the tooltip's positioning context; read it directly
      // because a hidden tooltip has no offsetParent.
      var wrap = els.chart.parentElement.getBoundingClientRect();
      var scale = box.width / parseFloat(root.getAttribute("viewBox").split(" ")[2]);
      var px = (event.clientX - box.left) / scale - MARGIN.left;
      var mu = xMin + (px / plotW) * (xMax - xMin);
      var value = macAt(mu, data.macc.a, data.macc.d);
      hover.setAttribute("opacity", 1);
      hoverLine.setAttribute("x1", x(mu));
      hoverLine.setAttribute("x2", x(mu));
      hoverDot.setAttribute("cx", x(mu));
      hoverDot.setAttribute("cy", y(value));
      els.tooltip.classList.remove("hidden");
      els.tooltip.textContent = "μ " + fmtPct(mu) + " — MAC " + fmtMoney(value);
      els.tooltip.style.left = (event.clientX - wrap.left) + "px";
      els.tooltip.style.top = (box.top - wrap.top + (y(value) + MARGIN.top) * scale) + "px";
    });
    capture.addEventListener("mouseleave", function () {
      hover.setAttribute("opacity", 0);
      els.tooltip.classList.add("hidden");
    });

    els.chart.appendChild(root);
  }

  function macAt(muPct, a, d) {
    var mu = muPct / 100;
    return a * mu + d * Math.pow(mu, 4);
  }

  // ---------------------------------------------------------------- verdicts

  var STATUS_TEXT = {
    over: "Over-abating",
    under: "Under-abating",
    on_target: "On target"
  };

  function renderVerdicts(data) {
    clear(els.verdicts);
    data.verdicts.forEach(function (verdict) {
      var card = document.createElement("div");
      card.className = "verdict " + verdict.status;

      var head = document.createElement("div");
      head.className = "head";
      head.textContent = verdict.measure_label + " vs. " + verdict.benchmark_label;
      card.appendChild(head);

      var call = document.createElement("div");
      call.className = "call";
      call.textContent = STATUS_TEXT[verdict.status] || verdict.status;
      if (verdict.status !== "on_target") {
        var gap = Math.abs(verdict.gap);
        call.textContent += " by " + gap.toFixed(gap < 10 ? 2 : 1) + " pts";
      }
      card.appendChild(call);

      var detail = document.createElement("div");
      detail.className = "detail";
      var parts = [
        "realized " + fmtPct(verdict.realized_mu) + " vs. optimum " + fmtPct(verdict.target_mu)
      ];
      if (verdict.ratio !== null && verdict.ratio !== undefined && isFinite(verdict.ratio)) {
        parts.push((verdict.ratio * 100).toFixed(0) + "% of the optimum");
      }
      if (verdict.forgone_net_benefit !== null && verdict.forgone_net_benefit !== undefined) {
        parts.push("forgone net benefit " + fmtMoney(verdict.forgone_net_benefit) + "/tCO₂ of BAU");
      }
      detail.textContent = parts.join(" · ");
      card.appendChild(detail);

      els.verdicts.appendChild(card);
    });
  }

  function renderDetails(data) {
    clear(els.details);

    var rows = [];
    data.benchmarks.forEach(function (item) {
      rows.push([item.label, item.mu, item.scc, "Model optimum"]);
    });
    data.measures.forEach(function (item) {
      var range = (item.low !== null && item.high !== null)
        ? "95% CI " + fmtPct(item.low) + " to " + fmtPct(item.high)
        : "no CI available";
      rows.push([item.label + " (realized)", item.mu, item.mac, range]);
    });

    var table = document.createElement("table");
    var thead = document.createElement("thead");
    thead.innerHTML =
      "<tr><th>Series</th><th class='num'>Abatement rate</th>" +
      "<th class='num'>$ / tCO₂ there</th><th>Note</th></tr>";
    table.appendChild(thead);

    var tbody = document.createElement("tbody");
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      [row[0], fmtPct(row[1]), fmtMoney(row[2]), row[3]].forEach(function (cell, index) {
        var td = document.createElement("td");
        if (index === 1 || index === 2) td.className = "num";
        td.textContent = cell;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    var heading = document.createElement("h2");
    heading.textContent = "Underlying values";
    els.details.appendChild(heading);
    els.details.appendChild(table);

    var macc = document.createElement("p");
    macc.className = "footnote";
    macc.textContent =
      "MACC coefficients: a = " + data.macc.a.toFixed(2) + ", d = " + data.macc.d.toFixed(2) +
      "  (MAC = a·μ + d·μ⁴, μ as a fraction).";
    els.details.appendChild(macc);

    if (data.warnings && data.warnings.length) {
      var warn = document.createElement("p");
      warn.className = "warnings";
      warn.textContent = data.warnings.join(" ");
      els.details.appendChild(warn);
    }
  }

  // ------------------------------------------------------------------- flow

  function renderChart() {
    if (!els.country.value) {
      clear(els.chart);
      clear(els.verdicts);
      clear(els.details);
      return Promise.resolve();
    }
    if (!selectedBenchmarks().length) {
      clear(els.chart);
      clear(els.verdicts);
      clear(els.details);
      setStatus("Select at least one benchmark.", true);
      return Promise.resolve();
    }
    var token = ++requestToken;
    setStatus("Loading…");
    return getJSON("/api/chart?" + query({ country: els.country.value }))
      .then(function (data) {
        if (token !== requestToken) return;
        setStatus(null);
        drawChart(data);
        renderVerdicts(data);
        renderDetails(data);
      })
      .catch(function (error) {
        if (token !== requestToken) return;
        clear(els.chart);
        clear(els.verdicts);
        clear(els.details);
        setStatus(error.message, true);
      });
  }

  function loadCountries() {
    var previous = els.country.value;
    return getJSON("/api/countries?" + query({})).then(function (payload) {
      clear(els.country);
      var withData = 0;
      payload.countries.forEach(function (country) {
        var option = document.createElement("option");
        option.value = country.code;
        option.textContent = country.name + (country.has_data ? "" : " (incomplete data)");
        option.disabled = !country.has_data;
        if (country.has_data) withData++;
        els.country.appendChild(option);
      });
      if (!withData) {
        setStatus("No country has complete data for this combination of year, "
          + "specification and measure.", true);
        return;
      }
      var options = Array.prototype.slice.call(els.country.options);
      var match = options.filter(function (o) { return o.value === previous && !o.disabled; })[0];
      var firstEnabled = options.filter(function (o) { return !o.disabled; })[0];
      els.country.value = (match || firstEnabled).value;
    });
  }

  function populateStatic() {
    meta.specs.forEach(function (spec) {
      var option = document.createElement("option");
      option.value = spec.key;
      option.textContent = spec.key + ". " + spec.label;
      els.spec.appendChild(option);
    });

    meta.years.forEach(function (year) {
      var option = document.createElement("option");
      option.value = year;
      option.textContent = year;
      els.year.appendChild(option);
    });
    if (meta.default_year) els.year.value = String(meta.default_year);

    if (meta.demo) els.demoBanner.classList.remove("hidden");
  }

  function refreshAll() {
    return loadCountries().then(renderChart).catch(function (error) {
      setStatus(error.message, true);
    });
  }

  function init() {
    getJSON("/api/meta").then(function (payload) {
      meta = payload;
      populateStatic();

      if (!meta.years.length) {
        setStatus(
          "No generated datasets found in " + meta.data_dir + ". Run "
          + "`python generate_cscc_vs_cntfc.py`, or restart the server with --demo.",
          true
        );
        return;
      }

      els.country.addEventListener("change", renderChart);
      [els.year, els.spec, els.measure].forEach(function (control) {
        control.addEventListener("change", refreshAll);
      });
      [els.nash, els.coop, els.focus].forEach(function (control) {
        control.addEventListener("change", renderChart);
      });

      refreshAll();
    }).catch(function (error) {
      setStatus("Could not reach the server: " + error.message, true);
    });
  }

  init();
})();
