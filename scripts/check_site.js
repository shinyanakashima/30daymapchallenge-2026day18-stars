// Open the built site, report console errors and failed requests, save screenshots.
// usage: node scripts/check_site.js [baseUrl] [outDir]
const { chromium } = require("playwright");

(async () => {
  const base = process.argv[2] || "http://localhost:8000/";
  const out = process.argv[3] || "docs";
  const browser = await chromium.launch();
  const problems = [];
  async function open(viewport, file, opts = {}) {
    const page = await browser.newPage({ viewport, deviceScaleFactor: opts.dpr || 1 });
    page.on("console", (m) => { if (m.type() === "error") problems.push(`console: ${m.text()}`); });
    page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
    page.on("response", (r) => { if (r.status() >= 400) problems.push(`${r.status()} ${r.url()}`); });
    page.on("requestfailed", (r) => {
      const err = r.failure()?.errorText || "";
      if (!err.includes("ERR_ABORTED")) problems.push(`failed ${r.url()} ${err}`); // tiles cancelled while moving
    });
    await page.goto(base + (opts.query || ""), { waitUntil: "networkidle" });
    await page.waitForTimeout(2500);
    if (opts.action) await opts.action(page);
    await page.screenshot({ path: `${out}/${file}` });
    await page.close();
  }
  await open({ width: 1200, height: 900 }, "screenshot.png");
  if (process.env.EXTRA) {
    await open({ width: 1200, height: 900 }, "check-ja.png", {
      query: "?lang=ja",
      action: async (p) => {
        await p.check("#overlay");
        await p.mouse.click(820, 300);
        await p.waitForTimeout(800);
      },
    });
    await open({ width: 390, height: 844 }, "check-mobile.png", { dpr: 2 });
    await open({ width: 1200, height: 900 }, "check-zoom.png", {
      action: async (p) => {
        await p.click("#places button");
        await p.waitForTimeout(5000);
      },
    });
  }
  await browser.close();
  if (problems.length) {
    console.log(problems.join("\n"));
    process.exit(1);
  }
  console.log("no console errors, no failed requests");
})();
