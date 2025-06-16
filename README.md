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
| **Gradle 8+** | build automation (wrapper bundled) | none – wrapper auto-downloads |
| **Fabric Loader & Fabric API** | modding platform | grab installer from <https://fabricmc.net> |
| **Python 3.9+** | run the AI server | <https://python.org> |
| *(optional)* CUDA toolkit | GPU inference for `llama-cpp-python` | see library docs |

---
## 1. Build & run the Minecraft mod

```bash
# clone and generate sources (first time only)
./gradlew :MC_AI_Project:genSources

# run the client with the mod on the classpath
./gradlew :MC_AI_Project:runClient
```

*The first build may download ~100 MB of Maven deps.
Subsequent invocations are incremental.*

**Dedicated server**
```bash
./gradlew :MC_AI_Project:runServer
```
(The mod works identically in single-player or on a Fabric server.)

After the client starts you should see
```
[AiCraft] WebSocket connected
```
in the game log.

---
## 2. Start the AI server

```bash
cd python_ai
python -m venv .venv && source .venv/bin/activate  # (optional) virtual-env
pip install -r requirements.txt --upgrade

# FAST CPU build of llama-cpp (no CUDA)
export LLAMA_MODEL=~/models/Meta-Llama-3-8B-instruct.Q4_K_M.gguf   # path to your GGUF
python main.py
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