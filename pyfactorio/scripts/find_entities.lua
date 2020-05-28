function find_entities(x1,y1, x2,y2)
  local ret = {}
  local surf=game.get_surface('nauvis')
  local ents = surf.find_entities({{x1, y1}, {x2,y2}})
  for k,v in pairs(ents) do
    ret[k] = {position = v.position; type = v.type; name = v.name}
    if v.type == 'resource' then -- v.mineable then
      ret[k].amount = v.amount
    end
  end
  return ret
end

_G.find_entities = find_entities
