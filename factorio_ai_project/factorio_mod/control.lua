-- This event is fired once when a new save is created or the mod is added.
-- It is the correct place to initialize the persistent data table.
script.on_init(function()
  -- Use the modern 'storage' global, which is best practice.
  storage.state = {
    tick_counter = 0,
    is_waiting_for_response = false
  }
end)

-- This event is fired when a save game with this mod is loaded.
script.on_load(function()
  -- To prevent crashes on loading old saves that might not have our data,
  -- we re-initialize the state if it's missing.
  if storage.state == nil then
    storage.state = {
      tick_counter = 0,
      is_waiting_for_response = false
    }
  end
end)

-- This single function handles all the game events we care about.
script.on_event({defines.events.on_tick, defines.events.on_http_request_completed}, function(event)
  -- If our state doesn't exist for some reason, do nothing.
  if storage.state == nil then return end

  -- == Handle HTTP Response from the AI Brain (highest priority) ==
  if event.name == defines.events.on_http_request_completed then
    storage.state.is_waiting_for_response = false -- We are no longer waiting
    
    if event.response then
      local success, response_body = pcall(game.json_to_table, event.response.content or "{}")
      if success and response_body and response_body.text then
        game.print("[AI BRAIN]: " .. response_body.text)
      else
        game.print("[AI BRAIN]: Received an invalid or empty JSON response.")
      end
    else
      game.print("[AI BRAIN]: Connection Failed. Is the Python server running?")
    end
    return -- We've handled the response, nothing more to do this tick.
  end

  -- == Handle Game Tick (sends the request to the AI) ==
  if event.name == defines.events.on_tick then
    -- Do nothing if we are already waiting for a response from the AI
    if storage.state.is_waiting_for_response then
      return
    end
    
    -- We will trigger the AI once every 2 seconds (120 ticks)
    storage.state.tick_counter = storage.state.tick_counter + 1
    if storage.state.tick_counter < 120 then
      return
    end
    
    -- Reset counter and set the flag that we are now waiting for the AI
    storage.state.tick_counter = 0
    storage.state.is_waiting_for_response = true

    local player = game.players[1]
    if not player then
      storage.state.is_waiting_for_response = false -- a player is required
      return
    end

    -- 1. Get Player Inventory
    local inventory_contents = {}
    local main_inventory = player.get_inventory(defines.inventory.character_main)
    if main_inventory and main_inventory.is_valid() then
      for _, item_stack in ipairs(main_inventory.get_contents()) do
        inventory_contents[item_stack.name] = (inventory_contents[item_stack.name] or 0) + item_stack.count
      end
    end

    -- 2. Scan Nearby Entities
    local nearby_entities = {}
    local scan_radius = 10 -- A 20x20 box around the player
    local scan_area = {
      left_top = {x = player.position.x - scan_radius, y = player.position.y - scan_radius},
      right_bottom = {x = player.position.x + scan_radius, y = player.position.y + scan_radius}
    }
    local found_entities = player.surface.find_entities_filtered{area = scan_area, type = {"tree", "resource"}}
    
    for _, entity in ipairs(found_entities) do
      local name = entity.name
      nearby_entities[name] = (nearby_entities[name] or 0) + 1
    end

    -- 3. Construct the data payload (the "spy report")
    local request_body_table = {
      player = {
        position = {x = player.position.x, y = player.position.y},
        inventory = inventory_contents
      },
      nearby_environment = {
        entities = nearby_entities
      }
    }

    local request_body_json = helpers.table_to_json(request_body_table)
    
    -- The address of our Python server running on the VM
    local url = "http://192.168.68.84:8000/"

    game.print("Sending status to AI Brain...")

    game.http_request({
      url = url,
      method = "POST",
      headers = {["Content-Type"] = "application/json"},
      content = request_body_json
    })
  end
end)
