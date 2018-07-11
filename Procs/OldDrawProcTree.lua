-- Config
KeyScrollUp      = "numpad-"
KeyScrollDown    = "numpad+"

KeyExpandName    = "numpad*"
KeyShrinkName    = "numpad/"

KeyToggleBack    = "numpad9"
KeyDump          = "numpad7"

KeyResetSettings = "numpad."

KeyToggleDisplay = {
	"numpad0",
	"numpad1",
	"numpad2",
	"numpad3",
	"numpad4",
	"numpad5"
}

MaxTreeDepth = 10

DefaultNameLen = 18
DefaultY = 4

-- Data Stuff
GameCode = ""

for i = 0, 3 do
	GameCode = GameCode .. string.char(memory.readbyte(0x080000AC + i))
end

Main6CRootArray = -1
SleepCallback   = -1
Main6CArraySize = 0
Custom6CNames = {}

if GameCode == "BE8E" then 
	-- FE8U
	
	Main6CRootArray = 0x02026A70
	SleepCallback   = 0x08003291
	Main6CArraySize = 6
	
elseif GameCode == "AE7E" then
	-- FE7U
	
	Main6CRootArray = 0x02026A30
	SleepCallback   = -1
	Main6CArraySize = 6
		
	Custom6CNames[0x8B924BC] = "Game Control"
	Custom6CNames[0x8CE3C54] = "Main Menu Logic"

elseif GameCode == "AE7J" then
	-- FE7J
	
	Main6CRootArray = 0x02026A28
	SleepCallback   = -1
	Main6CArraySize = 6
	
	Custom6CNames[0x8C01744] = "Game Control"
	Custom6CNames[0x8C01DBC] = "Map Main Logic"
	Custom6CNames[0x8C02630] = "Player Phase Logic"
	Custom6CNames[0x8C02870] = "Move Range Gfx"
	Custom6CNames[0x8C05464] = "[MAPTASK]"
	Custom6CNames[0x8D64F4C] = "Moving Unit Gfx"
	Custom6CNames[0x8DAD3A4] = "Main Menu Logic"
	Custom6CNames[0x8C09BF4] = "Any Menu"
	Custom6CNames[0x8C09C34] = "Menu Command"
	Custom6CNames[0x8D8B2D8] = "Goal Box"
	Custom6CNames[0x8D8B1A0] = "Terrain Box"
	Custom6CNames[0x8D8B200] = "Minimug Box"
end

-- Graphics Stuff
CurrentDrawLine = 0
NameLen = DefaultNameLen

DisplayBack = false

xOrigin = 4
yOrigin = DefaultY

DisplayTable = {
	true, true, true, true, true, true
}

DumpFile = nil
PreviousInput = input.get()

function PrintLine(Depth, String)
	DumpFile:write(string.rep("  ", Depth) .. String, "\n")
end

function DrawLine(Depth, String)
	if DumpFile == nil then
		local x = (xOrigin + 8*Depth)
		local y = (yOrigin + 8*CurrentDrawLine)
		
		gui.text(x, y, String)
		CurrentDrawLine = CurrentDrawLine + 1
	else
		PrintLine(Depth, String)
	end
end

function HandleInput()
	local Input = input.get()
	
	if Input[KeyScrollUp] and not PreviousInput[KeyScrollUp] then
		yOrigin = yOrigin - 8
	end
	
	if Input[KeyScrollDown] and not PreviousInput[KeyScrollDown] then
		yOrigin = yOrigin + 8
	end
	
	if Input[KeyExpandName] and not PreviousInput[KeyExpandName] then
		NameLen = NameLen + 2
	end
	
	if Input[KeyShrinkName] and not PreviousInput[KeyShrinkName] then
		NameLen = NameLen - 2
	end
	
	if Input[KeyToggleBack] and not PreviousInput[KeyToggleBack] then
		DisplayBack = not DisplayBack
	end
	
	for i = 1,6 do
		if Input[KeyToggleDisplay[i]] and not PreviousInput[KeyToggleDisplay[i]] then
			DisplayTable[i] = not DisplayTable[i]
		end
	end
	
	-- if Input[KeyDump] and not PreviousInput[KeyDump] then
		-- DumpFile = io.open("6CDump.txt", "a")
		
		-- DumpFile:write("\n\n", "6C DUMP, GAME: ", GameCode, "\n\n")
		
		-- DrawTableFooter()
		
		-- for i = 1, Main6CArraySize do
			-- if DisplayTable[i] then
				-- DrawRoot(Main6CRootArray + (i-1)*4)
			-- end
		-- end
		
		-- DumpFile:close()
		-- DumpFile = nil
	-- end
	
	if Input[KeyResetSettings] and not PreviousInput[KeyResetSettings] then
		NameLen = DefaultNameLen
		yOrigin = DefaultY
		
		DisplayBack  = false
		DisplayTable = { true, true, true, true, true, true }
	end
	
	PreviousInput = Input
end

function PaddedString(String, MinLen)
	if String:len() < MinLen then
		String = String .. string.rep(" ", MinLen - String:len())
	end
	
	return String
end

function ReadName(Pointer)
	if Pointer == 0 then
		return ""
	end
	
	local Result = ""
	
	while true do
		local NewChar = memory.readbyte(Pointer)
		
		if NewChar == 0 then
			break
		end
		
		Result = Result .. string.char(NewChar)
		
		Pointer = Pointer + 1
	end
	
	return Result
end

function ReadStructName(Struct)
	local Pointer = memory.readlong(Struct+0x10)
	local Result = ""
	
	if not (Pointer == 0) then
		Result = ReadName(Pointer)
	end
	
	if Result == "" then
		local Name = Custom6CNames[memory.readlong(Struct)]
		
		if Name == nil then
			Result = "----"
		else
			Result = Name
		end
	end
	
	return Result
end

function GetHaltString(Struct)
	HaltStack = memory.readbyte(Struct+0x28)
	
	if HaltStack == 0 then
		if memory.readlong(Struct+0x0C) == SleepCallback then
			SleepTimer = memory.readbyte(Struct+0x28)
			return "S:" .. SleepTimer
		else
			return "R"
		end
	else
		return "P:" .. HaltStack
	end
end

function GetStructString(Struct, MinNameLen)
	local StartPtr   = memory.readlong(Struct+0x00)
	local CurrentPtr = memory.readlong(Struct+0x04)
	
	local Name       = ReadStructName(Struct)
	local HaltString = GetHaltString(Struct)
	
	return string.format("%s %X+%X (%s)", PaddedString(Name, MinNameLen), StartPtr, (CurrentPtr - StartPtr), HaltString)
end

function DrawStruct(Depth, Struct)
	if Depth > MaxTreeDepth then
		DrawLine(Depth, "[...]")
	elseif not (Struct == 0) then
		DrawLine(Depth, GetStructString(Struct, NameLen - 2*Depth))
		
		-- Drawing Children
		DrawStruct(Depth + 1, memory.readlong(Struct+0x18))
		
		-- Drawing Next
		DrawStruct(Depth + 0, memory.readlong(Struct+0x20))
	end
end

function DrawTableFooter()
	DrawLine(0, PaddedString("Name", NameLen) .. " pointer+pc")
end

function DrawRoot(RootPointer)
	if not (memory.readlong(RootPointer) == 0) then
		DrawLine(0, "ROOT #" .. ((RootPointer - Main6CRootArray)/4))
		DrawStruct(1, memory.readlong(RootPointer))
	end
end

while true do
	HandleInput()
	
	if DisplayBack then
		gui.rect(1, 1, 238, 158, 0x00000080, 0x00000000)
	end
	
	CurrentDrawLine = 0
		
	for i = 1, Main6CArraySize do
		if DisplayTable[i] then
			DrawRoot(Main6CRootArray + (i-1)*4)
		end
	end
	
	if CurrentDrawLine < 18 then
		CurrentDrawLine = 18
		DrawTableFooter()
	end
	
	emu.frameadvance()
end
