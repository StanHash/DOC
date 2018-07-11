Command_EirikaMode:
	push {lr}
	
	ldr r0, =pChapterDataStruct @ 0202BCF0
	
	movs r1, #2 @ Eirika mode
	strb r1, [r0, #0x1B] @ Chapter Data + 0x1B is current mode
	
	ldr r0, =0xC17 @ "Will you go with Eirika?[N][Yes][X]" text id
	bl SetEventSlotC @ 0800D1F8 | Arguments: r0 = Value
	
	@ Return value = (0x1 = ???) | (0x2 = kill menu) | (0x4 = play beep sound) | (0x10 = clears menu graphics)
	mov r0, #0x17
	
	pop {r1}
	bx r1
