local function get_direction(from, to, distance)
    local dx = from.x - to.x
    local dy = from.y - to.y
    if dx > distance then
        -- west
        if dy > distance then
            return defines.direction.northwest
        elseif dy < -distance then
            return defines.direction.southwest
        else
            return defines.direction.west
        end
    elseif dx < -distance then
        -- east
        if dy > distance then
            return defines.direction.northeast
        elseif dy < -distance then
            return defines.direction.southeast
        else
            return defines.direction.east
        end
    else
        -- north/south
        if dy > distance then
            return defines.direction.north
        elseif dy < -distance then
            return defines.direction.south
        end
    end
    return nil
end

_G.get_direction = get_direction 
