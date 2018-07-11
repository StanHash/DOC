CallRouteSplitMenu:
	push {r4, lr}
	
	@ Saving argument from r0 to r4 (The Event Engine 6C)
	movs r4, r0
	
	bl ClearBG0BG1 @ 0804E884

	ldr  r2, =pLCDControlBuffer @ 03003080
	ldrb r0, [r2, #1]
	
	mov r1, #1
	orr r0, r1 @ enable bg0 display
	
	mov r1, #2
	orr r0, r1 @ enable bg1 display
	
	mov r1, #4
	orr r0, r1 @ enable bg2 display
	
	mov r1, #8
	orr r0, r1 @ enable bg3 display
	
	mov r1, #0x10
	orr r0, r1 @ enable obj display
	
	strb r0, [r2, #1]
	
	@ Setting up relevant graphics (Setting up text font and loading UI frame graphics)
	
	mov r0, #0
	bl SetFont @ 08003D38 | Arguments: r0 = Font Struct (0 for default)
	
	bl SetupFontForUI @ 080043A8
	
	bl LoadNewUIGraphics @ 0804EB68

	@ Calling the actual lord split menu 6C, with the event engine as parent
	
	ldr r0, =pRouteSplitMenuDef @ 089F36A0
	mov r1, r4
	bl NewMenu_DefaultChild @ 0804EBC8 | Arguments: r0 = Menu Def, r1 = Parent

	pop {r4}
	
	pop {r0}
	bx r0
