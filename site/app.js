(() => {
  "use strict";

  const T = {
    en: {
      title: "Where the light is null, the stars appear.",
      lead: "Japan drawn only with stars. The darker the night around a place, the more stars it gets; bright cities become empty patches. There are no place names: the coast and the cities show through the density of stars alone.",
      overlay: "Cities and coastline",
      legendTitle: "Night-sky classes",
      legendHint: "Stars drawn per 10 × 10 km",
      placesTitle: "Places with many stars",
      aboutTitle: "How this map was made",
      collapse: "Show or hide the panel",
      notesShort: "Star counts are rough figures set from night lights, not the stars you can actually see. Clouds, moonlight and seasons are not considered.",
      source: "Sources: NASA Black Marble, Natural Earth",
      classes: ["Truly dark sky", "Rural sky", "Rural / suburban edge", "Suburban sky", "Bright suburban sky", "City sky"],
      infoClass: (c) => `Night-sky class ${c} of 6`,
      infoDrawn: "stars drawn per 10 × 10 km",
      infoBortle: (b, r) => `For a sky like this (about Bortle ${b}), guides quote roughly ${r} stars visible to the naked eye.`,
      infoNone: "No stars drawn here",
      infoNoneText: "This point is sea or outside Japan.",
      infoNote: "A rough figure from night lights, not a count of the stars you would see.",
      about: `
        <p>Annual night lights from NASA Black Marble (VNP46A4, ${"{year}"}) were blurred over about 15 km, as a simple stand-in for the way town lights brighten the sky around them (no physical model). The blurred brightness was split into six classes. Each class was given a star density based on the rough number of stars said to be visible under the matching <a href="https://en.wikipedia.org/wiki/Bortle_scale" target="_blank" rel="noopener">Bortle scale</a> class, from thousands under a dark sky to a few dozen in a city. Stars were then scattered at random with a fixed seed, so the sky is the same every time.</p>
        <ul>
          <li>Star counts are rough figures set from night lights. They are not a calculation of the stars you can actually see.</li>
          <li>Clouds, moonlight and seasons are not taken into account.</li>
          <li>Sources: NASA Black Marble (VNP46A4, annual composite, ${"{year}"}); Natural Earth (coastline, cities). Both are in the public domain.</li>
        </ul>
        <p><a href="https://github.com/shinyanakashima/30daymapchallenge-2026day18-stars" target="_blank" rel="noopener">Source code and method</a></p>`,
    },
    ja: {
      title: "光がない場所に、星が現れる。",
      lead: "日本を星だけで描きました。夜の明かりが少ない場所ほど星を多く、明るい街ほど少なく描いています。地名はありません。星の濃淡だけで、海岸線と街の位置が浮かび上がります。",
      overlay: "都市名と海岸線",
      legendTitle: "夜空の段階",
      legendHint: "10km四方に描いた星の数",
      placesTitle: "星が多い場所",
      aboutTitle: "この地図のつくり方",
      collapse: "パネルの表示・非表示",
      notesShort: "星の数は夜の明かりから決めた目安で、実際に見える星の数ではありません。雲、月明かり、季節は考慮していません。",
      source: "出典: NASA Black Marble、Natural Earth",
      classes: ["とても暗い空", "農村の空", "農村と郊外の境目", "郊外の空", "明るい郊外の空", "街の空"],
      infoClass: (c) => `夜空の段階 ${c}（6段階中）`,
      infoDrawn: "個（10km四方に描いた星の数）",
      infoBortle: (b, r) => `このくらいの空（ボートルスケール ${b} 程度）では、肉眼で見える星はおよそ ${r} 個と紹介されています。`,
      infoNone: "星は描いていません",
      infoNoneText: "海、または日本の外です。",
      infoNote: "夜の明かりから決めた目安で、実際に見える星を数えたものではありません。",
      about: `
        <p>NASA Black Marble の年平均の夜間光（VNP46A4、${"{year}"}年）を半径約15kmでぼかし、街の光が周りの空を明るくする様子の代わりとしました（物理的な計算はしていません）。ぼかした明るさを6段階に分け、段階ごとに、夜空の暗さの目安「<a href="https://ja.wikipedia.org/wiki/%E3%83%9C%E3%83%BC%E3%83%88%E3%83%AB%E3%83%BB%E3%82%B9%E3%82%B1%E3%83%BC%E3%83%AB" target="_blank" rel="noopener">ボートルスケール</a>」で紹介されているおおよその星の数（暗い場所で数千個、都市で数十個）をもとに星の密度を決めました。星は種を固定した乱数で散らしているので、毎回同じ星空になります。</p>
        <ul>
          <li>星の数は夜の明かりから決めた目安で、実際に見える星の数を計算したものではありません。</li>
          <li>雲、月明かり、季節は考慮していません。</li>
          <li>出典: NASA Black Marble（VNP46A4 年合成、${"{year}"}年）、Natural Earth（海岸線、都市）。いずれもパブリックドメインです。</li>
        </ul>
        <p><a href="https://github.com/shinyanakashima/30daymapchallenge-2026day18-stars" target="_blank" rel="noopener">ソースコードと処理の方法</a></p>`,
    },
  };

  const PLACES = [
    { id: "rikubetsu", lon: 143.7385, lat: 43.4683, z: 8.6,
      en: ["Rikubetsu, Tokachi", "The \"town of stars\" in eastern Hokkaido, home to the Ginga-no-Mori observatory."],
      ja: ["陸別町（十勝）", "「星空の町」。銀河の森天文台がある、北海道東部の町。"] },
    { id: "achi", lon: 137.7470, lat: 35.4430, z: 8.6,
      en: ["Achi, Nagano", "A mountain village in southern Nagano known for its starry nights."],
      ja: ["阿智村（長野県）", "星空で知られる、長野県南部の山あいの村。"] },
    { id: "bisei", lon: 133.5600, lat: 34.6750, z: 8.8,
      en: ["Bisei, Okayama", "Passed one of Japan's first ordinances against light pollution, in 1989."],
      ja: ["美星町（岡山県井原市）", "1989年に全国でも早く光害防止の条例をつくった町。"] },
    { id: "kozushima", lon: 139.1370, lat: 34.2110, z: 9.2,
      en: ["Kozushima, Tokyo", "An island in the Izu chain, certified as a Dark Sky Place."],
      ja: ["神津島（東京都）", "伊豆諸島の島。星空保護区に認定されています。"] },
    { id: "iriomote", lon: 123.8100, lat: 24.3300, z: 8.6,
      en: ["Iriomote and Ishigaki, Okinawa", "Japan's first Dark Sky Park, at the southwestern end of the country."],
      ja: ["西表島・石垣島（沖縄県）", "日本で最初に星空保護区に認定された、国内の南西の端。"] },
  ];

  const qs = new URLSearchParams(location.search);
  let lang = qs.get("lang") === "ja" ? "ja" : "en";
  if (!qs.get("lang")) {
    try { lang = localStorage.getItem("stars-lang") === "ja" ? "ja" : "en"; } catch (_) { /* storage blocked */ }
  }

  let meta = null;
  let lookup = null;
  let lastClick = null;
  const fmt = (n) => new Intl.NumberFormat(lang === "ja" ? "ja-JP" : "en-US").format(n);
  const perSquare = (c) => Math.round(c.visible * meta.stars_per_km2_per_visible * 100);

  const map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {
        stars: {
          type: "raster", tiles: ["tiles/{z}/{x}/{y}.png"], tileSize: 256,
          minzoom: 3, maxzoom: 10, bounds: [122.5, 24.0, 149.0, 46.0],
          attribution: "Night lights: <a href=\"https://blackmarble.gsfc.nasa.gov/\" target=\"_blank\" rel=\"noopener\">NASA Black Marble</a> · <a href=\"https://www.naturalearthdata.com/\" target=\"_blank\" rel=\"noopener\">Natural Earth</a>",
        },
        coast: { type: "geojson", data: "data/coastline.geojson" },
      },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": "#000" } },
        { id: "stars", type: "raster", source: "stars", paint: { "raster-fade-duration": 200, "raster-resampling": "linear" } },
        { id: "coast", type: "line", source: "coast", layout: { visibility: "none" },
          paint: { "line-color": "#9fb4ff", "line-opacity": 0.28, "line-width": 0.6 } },
      ],
    },
    bounds: [[122.9, 24.0], [146.2, 45.6]],
    fitBoundsOptions: { padding: window.matchMedia("(max-width: 640px)").matches
      ? { top: 40, bottom: 90, left: 10, right: 10 }
      : { top: 30, bottom: 40, left: 370, right: 30 } },
    minZoom: 3, maxZoom: 12,
    attributionControl: { compact: true },
    dragRotate: false, pitchWithRotate: false,
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

  // city labels as HTML markers (no glyph server needed)
  const cityMarkers = [];
  fetch("data/cities.geojson").then((r) => r.json()).then((fc) => {
    fc.features.forEach((f) => {
      const el = document.createElement("div");
      el.className = "city";
      el.dataset.en = f.properties.en;
      el.dataset.ja = f.properties.ja;
      el.textContent = f.properties[lang];
      cityMarkers.push(new maplibregl.Marker({ element: el, anchor: "left" }).setLngLat(f.geometry.coordinates));
    });
    setOverlay(document.getElementById("overlay").checked);
  });

  function setOverlay(on) {
    if (map.getLayer("coast")) map.setLayoutProperty("coast", "visibility", on ? "visible" : "none");
    cityMarkers.forEach((m) => (on ? m.addTo(map) : m.remove()));
  }

  // sky-class lookup image
  Promise.all([
    fetch("data/meta.json").then((r) => r.json()),
    new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = "data/sky_class.png"; }),
  ]).then(([m, im]) => {
    meta = m;
    const cv = document.createElement("canvas");
    cv.width = im.width; cv.height = im.height;
    const ctx = cv.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(im, 0, 0);
    lookup = { data: ctx.getImageData(0, 0, im.width, im.height).data, w: im.width, h: im.height };
    render();
  });

  function classAt(lng, lat) {
    if (!lookup) return null;
    const b = meta.bbox;
    const x = Math.floor((lng - b.west) * meta.lookup_px_per_deg);
    const y = Math.floor((b.north - lat) * meta.lookup_px_per_deg);
    if (x < 0 || y < 0 || x >= lookup.w || y >= lookup.h) return 0;
    return Math.round(lookup.data[(y * lookup.w + x) * 4] / meta.lookup_scale);
  }

  function showInfo(lng, lat) {
    lastClick = [lng, lat];
    const t = T[lang];
    const c = classAt(lng, lat);
    const box = document.getElementById("info");
    const body = document.getElementById("info-body");
    const coord = `${lat.toFixed(3)}°N, ${lng.toFixed(3)}°E`;
    if (!c) {
      body.innerHTML = `<h3>${t.infoNone}</h3><p>${t.infoNoneText}</p><p class="muted">${coord}</p>`;
    } else {
      const k = meta.classes[c - 1];
      const n = perSquare(k);
      body.innerHTML = `<h3>${t.infoClass(c)} · ${t.classes[c - 1]}</h3>
        <p><span class="big">≈ ${fmt(n)}</span> ${t.infoDrawn}</p>
        <p>${t.infoBortle(k.bortle.replace("-", "–"), k.visible_range.replace("-", "–"))}</p>
        <p class="muted">${t.infoNote}</p>
        <p class="muted">${coord}</p>`;
    }
    box.hidden = false;
  }

  map.on("click", (e) => showInfo(e.lngLat.lng, e.lngLat.lat));
  document.getElementById("info-close").addEventListener("click", () => {
    document.getElementById("info").hidden = true; lastClick = null;
  });

  function drawSwatch(cv, density) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = 54 * dpr; cv.height = 16 * dpr;
    const ctx = cv.getContext("2d");
    let s = 1234;
    const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    const n = Math.round(density * 54 * 16 / 40);
    for (let i = 0; i < n; i++) {
      const r = rnd();
      ctx.fillStyle = `rgba(255,255,255,${0.45 + 0.55 * rnd()})`;
      const size = (r < 0.08 ? 1.6 : 0.9) * dpr;
      ctx.fillRect(rnd() * cv.width, rnd() * cv.height, size, size);
    }
  }

  function render() {
    const t = T[lang];
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t[el.dataset.i18n]; });
    document.querySelectorAll("[data-i18n-aria]").forEach((el) => el.setAttribute("aria-label", t[el.dataset.i18nAria]));
    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      el.innerHTML = t[el.dataset.i18nHtml].replaceAll("{year}", meta ? meta.year : "");
    });
    document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
    cityMarkers.forEach((m) => { const el = m.getElement(); el.textContent = el.dataset[lang]; });

    const legend = document.getElementById("legend");
    legend.innerHTML = "";
    if (meta) {
      meta.classes.forEach((k, i) => {
        const li = document.createElement("li");
        const cv = document.createElement("canvas");
        drawSwatch(cv, k.visible / 1000 * 4);
        const name = document.createElement("span");
        name.textContent = `${k.id}. ${t.classes[i]}`;
        const n = document.createElement("span");
        n.className = "n";
        n.textContent = `≈ ${fmt(perSquare(k))}`;
        li.append(cv, name, n);
        legend.append(li);
      });
      const hint = document.createElement("li");
      hint.innerHTML = `<span class="hint">${t.legendHint}</span>`;
      legend.append(hint);
    }

    const ul = document.getElementById("places");
    ul.innerHTML = "";
    PLACES.forEach((p) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.innerHTML = `<span class="pn"></span><span class="pd"></span>`;
      b.querySelector(".pn").textContent = p[lang][0];
      b.querySelector(".pd").textContent = p[lang][1];
      b.addEventListener("click", () => flyTo(p));
      li.append(b);
      ul.append(li);
    });
    document.title = lang === "ja" ? "光のない場所の星" : "Null Light, Stars";
    if (lastClick && !document.getElementById("info").hidden) showInfo(lastClick[0], lastClick[1]);
  }

  let placeMarker = null;
  function flyTo(p) {
    const small = window.matchMedia("(max-width: 640px)").matches;
    if (small) collapse(true);
    map.flyTo({ center: [p.lon, p.lat], zoom: p.z, speed: 1.4 });
    if (placeMarker) placeMarker.remove();
    const el = document.createElement("div");
    el.className = "place-mark";
    placeMarker = new maplibregl.Marker({ element: el }).setLngLat([p.lon, p.lat]).addTo(map);
    map.once("moveend", () => showInfo(p.lon, p.lat));
  }

  function collapse(on) {
    const panel = document.getElementById("panel");
    const btn = document.getElementById("collapse");
    panel.classList.toggle("collapsed", on);
    btn.setAttribute("aria-expanded", String(!on));
    btn.textContent = on ? "+" : "–";
  }
  document.getElementById("collapse").addEventListener("click", () => {
    collapse(!document.getElementById("panel").classList.contains("collapsed"));
  });
  if (window.matchMedia("(max-width: 640px)").matches) collapse(true);

  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
    lang = b.dataset.lang;
    try { localStorage.setItem("stars-lang", lang); } catch (_) { /* storage blocked */ }
    render();
  }));
  document.getElementById("overlay").addEventListener("change", (e) => setOverlay(e.target.checked));
  map.on("load", () => setOverlay(document.getElementById("overlay").checked));

  render();
})();
