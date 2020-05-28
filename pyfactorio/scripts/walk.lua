_G.walk_queue = Queue:new()
script.on_event(defines.events.on_tick, 
function() 
    local player = game.players[1]
    game.print('set walk1')
    local tgt = walk_queue:peek()
    if tgt then
      dir = get_direction(player.position, tgt, 0.5)
      if dir then
        game.players[1].walking_state = {walking = true, direction = dir}
      else
        walk_queue:get()
      end
    end
end)
