
00: END
---

    END

Ends the active event scene.

01: END2
---

    END2

Exact same as `END`.

02: SLEEP
---

    SLEEP Amount

Waits for `Amount` frames before continuing scene.

03: BACKGROUND
---

    BACKGROUND BackgroundId

Displays background identified by `BackgroundId`. If no background was displayed before, disables map sprites and weather effects.

Clears any displayed faces.

04: BACKGROUND_CONTINUED
---

    BACKGROUND_CONTINUED BackgroundId

Same as `BACKGROUND`, except this doesn't clear displayed faces.

05: DIALOGUE_CLEAR
---

    DIALOGUE_CLEAR

Clears any active faces and text boxes.

If a background is displayed, clears it and fades back to map, while restoring map sprites and weather effects.

06: FADE_FROM_SKIP
---

    FADE_FROM_SKIP

If scene-skipping, fades back to map. Typically used in battle map scenes just before `END` (and typically absent in world map scenes).

07: TEXT
---

    TEXT TextId

Displays dialogue text identified by `TextId`. Resets text-skipping.

This waits for the text to either end or return control to scene using `[Events]`. In the latter case, resume text using `TEXT_CONTINUE`.

08: TEXT_MORE
---

    TEXT_MORE TextId

Displays dialogue text identified by `TextId`. Does not display text if text-skipping.

This assumes it is after a `TEXT` and before a text-clearing code such as `DIALOGUE_CLEAR`.

09: TODO
---

0A: TEXT_CONTINUE
---

    TEXT_CONTINUE

Resumes text after a `[Events]` text code.

0B: CAMERA (position)
---

    CAMERA [X, Y]

Moves camera in such a way that the given map coordinates are visible and more than 2 tiles away from the edge (unless this would move the camera past the map edge, of course).

0C: CAMERA (character)
---

    CAMERA CharId

Moves camera in such a way that the unit corresponding to the given character is visible and more than 2 tiles away from the edge (unless this would move the camera past the map edge, of course).

0D: MOVE (from position)
---

    MOVE [XFrom, YFrom] [XTo, YTo]

Moves unit at `[XFrom, YFrom]` to `[XTo, YTo]`, and displays movement if not scene-skipping.

This event code does not wait for displayed movement to end before continuing (use `AWAIT_MOVE`).

0E: MOVE_MANUAL (from position)
---

    MOVE_MANUAL [XFrom, YFrom] MoveScript

Moves unit at `[XFrom, YFrom]` according to move script at address given by `MoveScript`, and displays movement if not scene-skipping.

This event code does not wait for displayed movement to end before continuing (use `AWAIT_MOVE`).

0F: MOVE (from character)
---

    MOVE CharId [XTo, YTo]

Moves unit corresponding to `CharId` to `[XTo, YTo]`, and displays movement if not scene-skipping.

This event code does not wait for displayed movement to end before continuing (use `AWAIT_MOVE`).

10: MOVE_MANUAL (from character)
---

    MOVE_MANUAL CharId MoveScript

Moves unit corresponding to `CharId` according to move script at address given by `MoveScript`, and displays movement if not scene-skipping.

This event code does not wait for displayed movement to end before continuing (use `AWAIT_MOVE`).

11: MOVE_NEXTTO
---

    MOVE_NEXTTO CharId ToCharId

Moves unit corresponding to `CharId` to a position adjacent to `ToCharId`, and displays movement if not scene-skipping.

This event code does not wait for displayed movement to end before continuing (use `AWAIT_MOVE`).

TODO: verify this isn't MOVE_ONTO.

12: LOAD
---

    LOAD Units

Loads unit group at address given by `Units`, and displays load movement if not scene-skipping.

This event code does not wait for displayed movement to end before continuing (use `AWAIT_MOVE`).

13: LOAD_INSTANT
---

    LOAD_INSTANT Units

Loads unit group at address given by `Units` at their final position, without displaying any movement.

14: AWAIT_MOVE
---

    AWAIT_MOVE

Waits for any displayed movement to finish.

15: CAMERA_FOLLOW_MOVE_ON
---

    CAMERA_FOLLOW_MOVE_ON

Enables having the camera follow moving units.

16: CAMERA_FOLLOW_MOVE_OFF
---

    CAMERA_FOLLOW_MOVE_OFF

Disables having the camera follow moving units

17: ASM
---

    ASM Function

Calls native function at address given by `Function`, with the address of the event engine proc as argument.

18: ASM_UNTIL
---

    ASM_UNTIL Function

Calls native function at address given by `Function`, with the address of the event engine proc as argument.

Repeat this every frame until the called function returns non-zero, or changes the active event cursor.

19: ASM_WHILE
---

    ASM_WHILE Function

Calls native function at address given by `Function`, with the address of the event engine proc as argument.

Repeat this every frame until the called function returns zero, or changes the active event cursor.

1A: STOP
---

    STOP

Stops the event engine without ending it (effectively making the game hang without support from external systems).

1B: LABEL
---

    LABEL LabelId

Marks the location of a label, which is a possible target for jump codes. This code does nothing by itself.

Label lookup is done by looking for each event code from the *start* of the current scene and getting the first matching label code.

Note that the lookup doesn't check for ends and whatnot. You could very well get the game into an endless loop if you look for a label that doesn't exist! (That or jump into a completely unrelated scene which may have interesting effects).

Label identifiers are 4 bytes and can range from 0 to `$FFFFFFFF`. There is no technical requirements when it comes to identifying labels other than that.

1C: GOTO
---

    GOTO LabelId

Jump to `LABEL` identified by `LabelId` unconditionally. For more information, see `LABEL`.

1D: GOTO_IFN_ALIVE
---

    GOTO_IFN_ALIVE LabelId CharId

Jump to `LABEL` identified by `LabelId` if unit corresponding to character `CharId` is not alive. For more information, see `LABEL`.

This doesn't care for non-player units.

1E: GOTO_IFN_DEPLOYED
---

    GOTO_IFN_DEPLOYED LabelId CharId

Jump to `LABEL` identified by `LabelId` if unit corresponding to character `CharId` is not deployed. For more information, see `LABEL`.

This doesn't care for non-player units.

1F: GOTO_IFY_ASM
---

    GOTO_IFY_ASM LabelId Function

Jump to `LABEL` identified by `LabelId` if called native function at address given by `Function` returns non-zero. For more information, see `LABEL`.

The called function gets the address of the event engine proc as first argument.

20: GOTO_IFN_ASM
---

    GOTO_IFN_ASM LabelId Function

Jump to `LABEL` identified by `LabelId` if called native function at address given by `Function` returns zero. For more information, see `LABEL`.

The called function gets the address of the event engine proc as first argument.

21: GOTO_IFY_SKIPPING
---

    GOTO_IFY_SKIPPING LabelId

Jump to `LABEL` identified by `LabelId` if scene-skipping or text-skipping. For more information, see `LABEL`.

22: GOTO_IFY_EID
---

    GOTO_IFY_EID LabelId Eid

Jump to `LABEL` identified by `LabelId` if eid corresponding to `Eid` is set. For more information, see `LABEL`.

23: GOTO_IFN_EID
---

    GOTO_IFN_EID LabelId Eid

Jump to `LABEL` identified by `LabelId` if eid corresponding to `Eid` is cleared. For more information, see `LABEL`.

24: GOTO_IFY_ACTIVE
---

    GOTO_IFY_ACTIVE LabelId CharId

Jump to `LABEL` identified by `LabelId` if unit corresponding to character `CharId` is the active unit. For more information, see `LABEL`.

25: JUMP
---

    JUMP Scene

Jump to scene at address given by `Scene`.

26: ITEM (to active unit)
---

    ITEM ItemId

Gives item identified by `ItemId` to active unit.

27: ITEM (to character)
---

    ITEM CharId ItemId

Gives item identified by `ItemId` to unit corresponding to character `CharId`.

28: MONEY
---

    MONEY Amount

Givens amount of money corresponding to `Amount` **to the active unit's team**.

29: MAPCHANGE
---

    MAPCHANGE MapChangeId

TODO...
