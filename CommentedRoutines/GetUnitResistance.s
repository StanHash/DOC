.thumb

GetUnitResistance:
	@ pushing registers
	push {r4, lr}
	
	@ Saving Unit in r4 (so we can use it later)
	mov r4, r0
	
	@ r0 is Unit, and the routine called here returns the item equipped for the unit in r0
	bl GetUnitEquippedWeapon
	
	@ this basically gets rid of the top 16 bits of the item. It's a compiler thing that you shouldn't worry about
	lsl r0, #0x10
	lsr r0, #0x10
	
	@ For the item in r0, gets it's resistance bonus
	bl GetItemResBonus
	
	@ Res bonus of equipped item is in r1
	mov r1, r0
	
	@ Unit Struct + 0x18 is where the unit personal resistance is stored
	@ So those two instruction get that value in r0
	mov  r0, #0x18
	ldsb r0, [r4, r0]
	
	@ Adding unit personnal res to the weapon res bonus
	add r0, r1
	
	@ Now loading the byte responsible for both the torch duration (not useful here) and the barrier/pure water duration
	add  r4, #0x31
	ldrb r1, [r4]
	
	@ erasing the first 4 bits of the byte (the torch bits), leaving only the barrier/pure water bits
	lsr r1, #4
	
	@ adding the result in r0
	add r0, r1
	
	@ the value in r0 will be interpreted as the result of this routine
	
	@ popping registers and returning to where we were called from
	pop {r4}
	pop {r1}
	bx r1
