# AI Craft – Minecraft + Llama-3 colony governor

This repository contains **two** cooperating parts:

1. `MC_AI_Project/` – a Fabric mod (Java 17) that runs inside Minecraft 1.20.6, sends a world snapshot to an external AI and applies the returned build-plan.
2. `python_ai/` – a tiny Flask + WebSocket server that loads a local **Llama 3** GGUF model (via `llama-cpp-python`) and decides what blocks to place.

The default behaviour is a "hello-world" loop: every two seconds the mod pushes a JSON snapshot (time-of-day, player-count) to the Python server; the server replies with a plan that places one oak plank at (0, 70, 0).

> Replace the echo logic with your own prompt engineering or RL agent to make the AI actually *play* the game.

---
## 0. Prerequisites (one-time)

| Tool | Why | Install |
|------|-----|---------|
| **Java 17 JDK** | compile the mod | <https://adoptium.net> |
| **Git for Windows** | clone / update the repo *(`git` command)* | <https://git-scm.com/download/win> *(or skip and use "Download ZIP")* |
| **Gradle 8+** | build automation (wrapper bundled) | none – wrapper auto-downloads |
| **Fabric Loader + Fabric API** | modding platform | installer at <https://fabricmc.net> |
| **Python 3.9+** | run the AI server | <https://python.org> |
| *(optional)* CUDA toolkit | GPU inference for `llama-cpp-python` | see library docs |

---
## 1. Build & run the Minecraft mod  (Windows 10/11)

Open an **"Developer PowerShell for VS"** (or regular PowerShell).  
If `git` is *not* recognised, either
1. Install **Git for Windows** (link above) and restart PowerShell, **or**
2. Click the green "**Code → Download ZIP**" button on GitHub, extract to `C:\Dev\AiCraft`, then start at step 1-b.

```powershell
# 1-a.  Clone the repo
> git clone https://github.com/LimmeDev/CoiAI.git C:\Dev\AiCraft
> cd C:\Dev\AiCraft

# 1-b.  First-time Gradle prep – this downloads Yarn mappings & Fabric jars
> .\gradlew.bat :MC_AI_Project:genSources   # ~100 MB, one-time only

# 1-c.  Launch the game with the mod on the classpath
> .\gradlew.bat :MC_AI_Project:runClient
```

(If **Windows SmartScreen** complains the first time you run `gradlew.bat`, click "More info → Run anyway"; it's just the Gradle wrapper.)

*The first build downloads Maven dependencies; subsequent launches are near-instant.*

### Running a dedicated Fabric **server**
```powershell
> .\gradlew.bat :MC_AI_Project:runServer
```
Server console appears; the AI functions the same in multiplayer.

When the client finishes loading you should see this in the log:
```
[AiCraft] WebSocket connected
```
which means the mod successfully opened the WebSocket to the Python AI.

---
## 2. Start the AI server

```powershell
cd python_ai

# 2-a.  (Recommended) create an isolated virtual-env
> python -m venv .venv
> .\.venv\Scripts\Activate.ps1        # prompt changes to (venv)

# 2-b.  Install deps (Flask + WebSocket + optional llama-cpp)
> pip install --upgrade -r requirements.txt

# 2-c.  Point to your downloaded GGUF model (or skip for echo mode)
> $env:LLAMA_MODEL = "C:\Models\Meta-Llama-3-8B-instruct.Q4_K_M.gguf"

# 2-d.  Run the server
> python main.py
```
Console output:
```
 * Serving Flask app 'main'
 * WS endpoint ready at ws://127.0.0.1:8000/ws …
```

Leave this terminal running while you play.

---
## 3. What should happen
1. Every ~2 seconds the Minecraft console prints
   ```
   [AiCraft] WebSocket connected
   [AiCraft] Posting snapshot …
   ```
2. The Python console logs the snapshot and sends a JSON plan back.
3. In-game you'll see oak planks appear at ground 70 near the world spawn.

---
## 4. Extending the snapshot & plan
Edit `AiCraft.java`:
```java
snap.put("biome", server.getOverworld().getBiome(spawnPos).value().getTranslationKey());
```
Return richer plans from Python:
```json
{
  "build": [
    {"block":"minecraft:oak_planks","x":0,"y":70,"z":0},
    {"block":"minecraft:torch","x":0,"y":71,"z":0}
  ],
  "chat": "Hello world!"
}
```
…and handle them in `applyPlan()`.

---
## 5. Packaging a distributable mod jar
```bash
./gradlew :MC_AI_Project:build
```
The jar appears in `MC_AI_Project/build/libs/`. Drop it into `.minecraft/mods/` for any Fabric install.

---
## 6. Common FAQ

**Q: Can this run on a Paper/Spigot/Bukkit server?**  
No. Fabric mods require Fabric Loader. Use **Geyser** or **Velocity** if you need proxy support.

**Q: Does the AI server have to run on the same PC?**  
No; change the URI in `AiCraft.java` to your LAN/WAN host and open the port.

**Q: How do I stop the AI?**  
Close the Python process or run `/reload` in-game to unload the mod.

---
Happy experimenting! 