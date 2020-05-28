Queue = {}
Queue.__index = Queue

function Queue:new()
  o = {
    first = 1;
    fresh = 1;
  }
  setmetatable(o, Queue)
  o.__index = self
  return o
end

function Queue:peek()
  return self[self.first]
end

function Queue:get()
  if self.first >= self.fresh then
    return nil
  else
    v = self[self.first]
    self[self.first] = nil
    self.first = self.first + 1
    return v
  end
end

function Queue:put(v)
  self[self.fresh] = v
  self.fresh = self.fresh + 1
end

_G.Queue = Queue
