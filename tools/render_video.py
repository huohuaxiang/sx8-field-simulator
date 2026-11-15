import asyncio, base64, os, sys, time
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(ROOT, "sx8-field-simulator.html")
OUT = os.path.join(ROOT, "video", "c")
W, H = 1280, 720
DT = 0.025          # 1/40 s of timeline per frame  -> 1.5x speed at 60 fps

async def main(start, count):
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel=None, executable_path=os.environ.get("CHROMIUM", "/usr/local/bin/chromium"),
            args=["--no-sandbox","--enable-unsafe-swiftshader","--use-angle=swiftshader",
                  "--disable-dev-shm-usage","--hide-scrollbars","--force-device-scale-factor=1"])
        pg = await b.new_page(viewport={"width":1920,"height":1080}, device_scale_factor=1)
        await pg.goto(URL + "?hud=1&capture=1&q=low", wait_until="load", timeout=90000)
        await pg.wait_for_function("window.SX8 && SX8.ready===true", timeout=120000)
        await pg.evaluate(f"()=>SX8.setBuffer({W},{H})")
        await pg.evaluate("""()=>{ const D=window.__SX8DBG;
            D.scene.traverse(o=>{ if(o.isLight && o.shadow){ o.shadow.mapSize.set(512,512);
                if(o.shadow.map){ o.shadow.map.dispose(); o.shadow.map=null; } } });
            D.renderer.shadowMap.needsUpdate = true; }""")
        # jump straight to the first frame of this shard (seek = single evaluation pass)
        t_start = start * DT
        await pg.evaluate("t=>{ SX8.seek(t); SX8.prefill(t); }", t_start)
        t0 = time.time()
        for i in range(start, start + count):
            await pg.evaluate(f"()=>SX8.advance({DT})")
            s = await pg.evaluate("()=>SX8.readJPEG(0.95)")
            raw = base64.b64decode(s.split(",", 1)[1])
            with open(f"{OUT}/{i:05d}.jpg", "wb") as fh:
                fh.write(raw)
            if i % 20 == 0:
                el = time.time() - t0
                done = i - start + 1
                print(f"frame {i}  {el:.0f}s  {el/done:.2f}s/f  eta {((start+count-i)*el/done)/60:.1f}min", flush=True)
        print("DONE", time.time() - t0, flush=True)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]), int(sys.argv[2])))
