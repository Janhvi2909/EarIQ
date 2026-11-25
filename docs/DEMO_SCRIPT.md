# EarIQ live demo (4–5 minutes)

## Before you present (5 minutes earlier)

1. Laptop **on the charger** (the speech model is heavy; low battery slows everything).
2. Start the app and keep this terminal open:
   ```bash
   cd ~/Desktop/NLP
   .venv/bin/uvicorn app.server:app --port 8000
   ```
3. Open **http://localhost:8000** in Chrome. Wait until the top-right pill says **Ready · runs on this device** (about 30–60 s).
4. Click **Number with a pause** once as a warm-up, so the first live result is fast.
5. Open a second tab at **http://localhost:8000/monitor**.
6. Allow the microphone when Chrome asks. Wi-Fi is **not** needed: everything runs on the laptop.

## The flow

| Step | Click / do | Say (short) |
|---|---|---|
| 1 | Home page, scroll a little | "Voice AI talks well but still mishears the details that matter: numbers, emails, names, IDs. EarIQ is a plug-in layer that fixes that." |
| 2 | Click **Number with a pause** | "The agent asked for a phone number. The caller pauses in the middle, which real people do." |
| 3 | Point at the left card's red **✂ Stopped listening** | "A typical voice AI uses a fixed silence timeout, so it cuts the caller off and saves nothing." |
| 4 | Point at the right card | "EarIQ knows a 10-digit number isn't finished after 5 digits, so it waits. It turns the words into the exact value, checks the format, and saves 98765 43210." |
| 5 | Click **Spelled name** | "Here the speech model mishears 'Kell' as 'Kel'. Normal AI saves the wrong name. EarIQ trusts the spelling the caller gave: Rina Kell, correct." |
| 6 | Click **Email, "at the rate"** | "Indian English says 'at the rate' for @. Normal AI can't parse it; EarIQ writes a proper email." |
| 7 | Pick **Phone**, press the mic, say *"My number is nine eight seven six five … (pause) … four three two one zero"* and press stop | Live, with your own voice. If it asks *"Just to confirm…"*, click **Yes**: "It only asks about the part it isn't sure of." |
| 8 | Scroll to **Measured, not promised** | "These come straight from our test results: fewer wrong values on 300 real recordings, fewer cut-offs while dictating, and less than one follow-up question per five answers." |
| 9 | Switch to the **Monitor** tab | "In production you watch latency, follow-up rate, errors and alerts. No audio is stored and values are masked." |

## If something goes wrong

- **Pill says "Loading model"** → wait 30 s. Still loading? Restart the server command.
- **Mic blocked** → use the four sample buttons; they show everything.
- **Live recording gives a wrong result** → say: "This is exactly why EarIQ asks or confirms instead of guessing", then use a sample.
- **Laptop or server fails completely** → play the backup video (below).

## Record the backup video (once, the day before)

1. Start the app as above and do the flow (steps 2–7).
2. Record with **QuickTime Player → File → New Screen Recording** (or press `Cmd + Shift + 5`), with the microphone on so the samples' audio is captured.
3. Save it as `EarIQ_demo.mov` on the Desktop and in Google Drive.
