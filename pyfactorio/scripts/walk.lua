_G.walk_queue = Queue:new()
script.on_event(defines.events.on_tick, 
function() 
    local player = game.players[1]
    if walk_queue:size() > 0 then
        game.print(string.format('Walk queue: %s', walk_queue:size()))
    end
    local tgt = walk_queue:peek()
    if tgt then
      dir = get_direction(player.position, tgt, 0.2)
      if dir then
        game.players[1].walking_state = {walking = true, direction = dir}
      else
        walk_queue:get()
      end
    end
end)
