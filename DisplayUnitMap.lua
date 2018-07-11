
UnitMap = 0x0202E4D8

gui.register(function()
	local UnitMapRows = memory.readlong(UnitMap)
	
	local CamX = memory.readshort(0x0202BCBC+0)
	local CamY = memory.readshort(0x0202BCBC+2)
	
	local MapW = memory.readshort(0x0202E4D4+0)
	local MapH = memory.readshort(0x0202E4D4+2)
	
	for iy = 1, MapH do
		local Row = memory.readlong(UnitMapRows + 4*(iy - 1))
		
		for ix = 1, MapW do
			local Tile = memory.readbyte(Row + (ix - 1))
			
			gui.text(ix * 16 - 12 - CamX, iy * 16 - 12 - CamY, string.format("%X", Tile))
		end
	end
end)
