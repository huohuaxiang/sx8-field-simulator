import sys, os, json, asyncio
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(ROOT, "sx8-field-simulator.html")
OUTDIR = os.path.join(ROOT, "_dev", "shots")
times = sys.argv[1:] or ["0.5"]

async def main():
    os.makedirs(OUTDIR, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel=None, executable_path=os.environ.get("CHROMIUM", "/usr/local/bin/chromium"),
            args=["--no-sandbox","--enable-unsafe-swiftshader","--use-angle=swiftshader",
                  "--disable-dev-shm-usage","--force-device-scale-factor=1"])
        pg = await b.new_page(viewport={"width":1600,"height":900}, device_scale_factor=1)
        errs = []
        pg.on("console", lambda m: errs.append((m.type, m.text)) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(("pageerror", str(e)))
        )
        await pg.goto(URL + "?hud=1&capture=1", wait_until="load", timeout=90000)
        await pg.wait_for_function("window.SX8 && window.SX8.ready===true", timeout=60000)
        for t in times:
            await pg.evaluate("t=>{SX8.frame(t)}", float(t))
            await pg.wait_for_timeout(250)
            await pg.screenshot(path=os.path.join(OUTDIR, f"t{float(t):05.2f}.png"))
            info = await pg.evaluate("""()=>{
              const cs=[...document.querySelectorAll('.collo')].map(e=>({o:getComputedStyle(e).opacity,l:e.style.left,t:e.style.top,w:e.offsetWidth,c:e.textContent}));
              return {t:window.SX8.time, callouts:cs.filter(c=>c.o!=='0').slice(0,4)};
            }""")
            print("shot", t, json.dumps(info, ensure_ascii=False)[:400])
        print("ERRS:", json.dumps(errs, ensure_ascii=False)[:1500])
        await b.close()

asyncio.run(main())
