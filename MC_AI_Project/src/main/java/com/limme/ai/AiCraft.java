package com.limme.ai;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.registry.Registries;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.util.HashMap;
import java.util.Map;

/**
 * AiCraft – a minimal Fabric mod that streams a JSON snapshot of the world
 * to a local Python/Llama service and applies the returned build plan.
 */
public class AiCraft implements ModInitializer {
    private static final Gson GSON = new GsonBuilder().create();
    private WebSocketClient socket;
    private int tickCounter = 0;

    @Override
    public void onInitialize() {
        // Delay socket until server is fully started so we have a reference
        ServerLifecycleEvents.SERVER_STARTED.register(this::onServerStarted);

        ServerTickEvents.START_SERVER_TICK.register(server -> {
            if (socket != null && socket.isOpen() && (++tickCounter % 40) == 0) {
                sendSnapshot(server);
            }
        });
    }

    private void onServerStarted(MinecraftServer server) {
        try {
            socket = new WebSocketClient(new URI("ws://127.0.0.1:8000/ws")) {
                @Override public void onOpen(ServerHandshake handshake) { log("WebSocket connected"); }
                @Override public void onMessage(String message)          { applyPlan(server, message); }
                @Override public void onClose(int c, String r, boolean b){ log("WebSocket closed");    }
                @Override public void onError(Exception ex)              { ex.printStackTrace();        }
            };
            socket.connect();
        } catch (Exception e) { e.printStackTrace(); }
    }

    /* ------------------------------------------------------ */
    /*  Snapshot -> Python                                     */
    /* ------------------------------------------------------ */
    private void sendSnapshot(MinecraftServer server) {
        Map<String, Object> snap = new HashMap<>();
        snap.put("dayTime", server.getOverworld().getTimeOfDay());
        snap.put("players", server.getPlayerManager().getPlayerList().size());
        String json = GSON.toJson(snap);
        socket.send(json);
    }

    /* ------------------------------------------------------ */
    /*  Plan <- Python                                         */
    /* ------------------------------------------------------ */
    private void applyPlan(MinecraftServer server, String json) {
        JsonObject plan;
        try { plan = JsonParser.parseString(json).getAsJsonObject(); }
        catch (Exception e) { log("Invalid JSON from AI"); return; }

        JsonArray builds = plan.getAsJsonArray("build");
        if (builds == null) return;

        for (var elem : builds) {
            JsonObject o = elem.getAsJsonObject();
            String id = o.get("block").getAsString();
            int x = o.get("x").getAsInt();
            int y = o.get("y").getAsInt();
            int z = o.get("z").getAsInt();

            Block block = Registries.BLOCK.get(new Identifier(id));
            BlockState state = block.getDefaultState();
            BlockPos pos = new BlockPos(x, y, z);

            server.execute(() -> server.getOverworld().setBlockState(pos, state));
        }
    }

    private static void log(String msg) { System.out.println("[AiCraft] " + msg); }
} 