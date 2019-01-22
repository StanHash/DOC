# Event Master Doc

The goal here is to have a complete and detailed documentation of how event scenes are handled by the base game, including a complete description of every known event code (except world map specific codes, for now).

When this is done, I will also post that on FEU. It isn't done yet tho so it will be only here for now.

Example and other event scene source will be written in event assembler language with no macros(*), and using [my experimental EA standard raws](https://github.com/StanHash/EAStandardLibrary/tree/experimental).

(*): As sole exception, I will be using the `sX` aliases for slot identifiers, to put emphasis on what is a slot identifier and what is a number.

## Generalities

### Code representation

The binary representation of each code is as follows:

	bits 0-3  | subcode : "subcode" identifier
	bits 4-7  | size    : byte size / 2
	bits 8-15 | id      : code identifier
	[code-dependent layout]

I'll simplify the representation of the header like so:

	[XXYZ]

With `XX` corresponding to the code id, `Y` to the code size and `Z` to the subcode. All in hexadecimal.

The size of a code in memory is *always* to be considered as equal to `size*2` bytes (header included), no matter what code this is. This is in contrast with FE6 and FE7 where to each code id is assigned a fixed size. This could allow for some funky obfucation shenanigans if you felt like doing that.

In this document, I will always use the size the code would have been if seen in vanilla events, which afaik is always its minimal size, aligned 4, for a given code id (and not subcode!).

The code identifier essentially dictates which routine the event engine will can to handle the code. The "subcode" doesn't have any meaning for the event engine itself, but usually it is used by the handling routine to know what kind of operation it needs to do.

For example, the code id `0x33` handles a whopping 9 subcodes, each of which reads some kind of information related to a unit. You can see that the general thing this code does is "reading information from a unit", but the subcode dictates which information to read (if it exists, if it is alive, which is its allegiance, its class id, its luck stat...).

### Event Slots

Event slots are objects available for storing and retrieving values. They persist for the duration of a scene and can often be used to pass values to event codes.

There are 14 of them, noted `s0` to `sD`. Some of them are special:

- `s0` always holds 0. More specifically, it is reset to 0 before each code is interpreted.
- `s1` typically holds "implicit code arguments". Codes that always read from a slot usually read from `s1`.
- `s2` typically holds "explicit code arguments". Codes that can substitute one of their fixed arguments for a slot value usually read from `s2`.
- `sB` typically holds "positions". Codes that can read positions from slot will read it from `sB`.
- `sC` typically holds "results". Codes that yield a result will store it in this slot.
- `sD` holds the queue size.

### Event Queue

The event queue is a list of values that follow a [FIFO](https://en.wikipedia.org/wiki/FIFO_(computing_and_electronics)) (First In First Out) model (hence why it's called a queue).

It can be (and is) used to pass lists of values to various codes and/or subscenes. `sD` should always hold the queue size. The queue can be manipulated using the `07 : queue operations` codes.

The event queue has room for up to 30 elements.

### Eids

Eids (aka "event ids" or "flags") are booleans that you can use to mark the completion of certain events. Many of them have set purpose but many others are free to be used for your chapter logic.

There are two kinds of eids:

- chapter (or "temporary") eids, which persist for the duration of a chapter and are saved accordingly. They are cleared upon switching chapters.
- global (or "permanent") eids, which persist for the duration of a given playthrough and are saved accordingly. They are only cleared upon starting a new game.

Note that eids are meant to be used as simple on/off switches. If you need to store other kind of numbers, consider maybe looking at counters.

[See this post for a detailed map of what eids are used for what purpose](https://feuniverse.us/t/fe8-eid-glossary/4815?u=stanh).

### Counters

Counters are small variables that can hold values ranging from 0 to 15 included. There is a total of 8 of them (identified by integers from 0 to 7). They persist for the duration of a chapter and are saved accordingly (much like chapter eids).

Counters can be manipulated using the `0F : counter operations` codes.

### Evbits

The event engine holds a set of internal flags called "evbits" which have various meanings. Many event codes implictely modify them, or behave differently based on their state. Here's the full list of known evbits:

- evbit `0` is the "ignore queued scenes" evbit. When set upon reaching the end of the current scene, queued scenes will not be executed and control will be given back to the main game logic.
- evbit `1` is the "scene is active" evbit? It is set before interpreting any event code. TODO: investigate further.
- evbit `2` is the "scene-skipping" evbit. It is automatically set by the event engine which the player presses start (unless evbit `4` is set)
- evbit `3` is the "text-skipping" evbit. It is set when the player presses Start or B during text (unless evbit `5` was set before the text was displayed)
- evbit `4` is the "prevent scene-skipping" evbit. When set, it prevents the player to scene-skip using Start. It can be modified by `10 : configure skipping`.
- evbit `5` is the "prevent text-skipping" evbit. When set, it prevents the player to text-skip using B or Start. It can be modified by `10 : configure skipping`.
- evbit `6` is the "prevent text-fast-forwarding" evbit. When set, it prevents the player to fast-forward the text using A, B or the D-pad. It can be modified by `10 : configure skipping`.
- evbit `7` is the "no end fade" evbit. When set, it prevents cutscene events to clear the screen when reaching the end. See related scene source in `01 : end` doc for further details.
- evbit `8` is the "faded in" evbit. Is is automatically set/cleared by the `17 : fade in/out` codes accordingly. It is set by `10 : configure skipping` when skipping is disabled but evbit `2` is set.
- evbit `9` is the "camera follows moving units" evbit. When set, any units moved through events (through loading or moving for example) will have the camera follow them.
- evbit `10` is the "moving to another chapter" evbit? Is is set by the "move to chapter" family of event codes. TODO: investigate further.
- evbit `11` is the "changing game mode" evbit? TODO: investigate further.
- evbit `12` is the "gfx locked" evbit. It is automatically set and unset by the "lock/unlock gfx" event codes.

evbits persist for the duration of a scene.

### Unit parameters

Most codes that work with units take character identifiers as parameters. There are some common rules this kind of parameter follow almost all of those codes follow (the only exception is TODO):

- When the argument is `0`, the unit taken into account is the player leader unit.
- When the argument is `-1`, the unit taken into account is the active unit.
- When the argument is `-2`, the unit taken into account is the unit at position in `sB`.
- When the argument is `-3`, the unit taken into account is the first unit whose character id corresponds to `s2`.
- Otherwise, the unit taken into account is the first unit whone character id corresponds to the argument.

## The Code Doc

This lists all event codes from 00 to 45 (hex) by id. The 80 to CD range may or may get documentation here in the future, just know that those are all world map related and probably not relevant to most people.

<details>
<summary>00 : do nothing (NOP)</summary>

```
[0020] NOP
```

Does nothing, doesn't seem to have any use.

---

</details>

<details>
<summary>01 : end (ENDA, ENDB)</summary>

```
[0120] ENDA
[0121] ENDB
```

- `ENDA` ends active event subscene. This means that if this scene was called using the `[0A40] CALL` event code, control will be given back to the calling event scene.
- `ENDB` ends event subscene and calling subscene(s). This means that if this scene was called using the `[0A40] CALL` event code, control *won't* be given back.

If evbit `0` is set, the event engine ends immediately, reguardless of whether this scene was called or not. Queued scenes won't be run either.

If no scene is returned to, and if the current scene "type" is "chapter cutscene", a special "cleanup" event scene will be called. Here's the full source for that scene:

<details>
<summary>Cleanup Scene Source</summary>

```
scAfterEnd:
  CHECK_EVBIT 10
  BNE $0 sC s0

  CALL scAfterEnd_Clean
  GOTO 1

LABEL $0
  CALL scAfterEnd_CleanResetMap

LABEL $1
  ENDA

scAfterEnd_Clean:
  CHECK_EVBIT 8
  BNE $0 sC s0

  CHECK_EVBIT 7
  BNE $63 sC s0

  FADI 0x10

LABEL $0
  CLEAN

  FADU 0x10

LABEL $63
  ENDA

scAfterEnd_CleanResetMap:
  CHECK_EVBIT 8
  BNE $0 sC s0

  FADI 0x10

LABEL $0
  CHECK_EVBIT 11
  BEQ $1 sC s0

  CHECK_CHAPTER_NUMBER

  SADD s2 sC s0 // s2 = sC
  SCOORD sB [0, 0]

  LOMA (-1)

LABEL $1
  ENDA
```

</details>

---

</details>

<details>
<summary>02 : set eid and evbits (ENUT, ENUF, EVBIT_T, EVBIT_F)</summary>

```
[0220] EVBIT_F Evbit
[0228] EVBIT_T Evbit
[0221] ENUF Eid
[0229] ENUT Eid
```

- `EVBIT_F` clears given evbit.
- `EVBIT_T` sets given evbit.
- `ENUF` clears given eid.
- `ENUT` sets given eid.

If the argument is negative, the target evbit/eid will be read from `s2`. EA standard raws provides the parameterless `ENUF_SLOT2` and `ENUT_SLOT2` codes for convenience.

---

</details>

<details>
<summary>03 : get eid and evbits (CHECK_EVBIT, CHECK_EVENTID)</summary>

```
[0320] CHECK_EVBIT Evbit @ gets Evbit state in sC
[0321] CHECK_EVENTID Eid @ gets Eid state in sC
```

The argument is allowed to be `(-1)`, in which case the target Evbit/Eid will be read from `s2`.

---

</details>

<details>
<summary>04 : get random number (RANDOMNUMBER)</summary>

```
[0420] RANDOMNUMBER Max
```

Gets random integer in interval `[0-Max]` in `sC`.

This uses the game's primary random number generator (the same one used for battle calculations). This is contrast to FE6 and FE7 where similar codes used the secondary ("cosmetic") random number generator.

If `Max` is 0, then the result will be `0`, and no random number will be generated.

`Max` is fixed and there is no way of having it read from an event slot.

---

</details>

<details>
<summary>05 : set slot value (SVAL)</summary>

```
[0540] SVAL Slot Value
```

Sets slot content to the give value.

EA standard raws provide `SMOV` and `SETVAL` as straight alias to `SVAL`. Experimental raws provide `SCOORD slot [X, Y]` and `SPTR Slot Offset` for convenience.

Setting `s0` has no effect (it will be reset to 0 before the next code is handled).

---

</details>

<details>
<summary>06 : math on slots (SADD, SSUB, SMUL, SDIV, SMOD, SAND, SORR, SXOR, SLSL, SLSR)</summary>

```
[0620] SADD sDest sSrc1 sSrc2
[0621] SSUB sDest sSrc1 sSrc2
[0622] SMUL sDest sSrc1 sSrc2
[0623] SDIV sDest sSrc1 sSrc2
[0624] SMOD sDest sSrc1 sSrc2
[0625] SAND sDest sSrc1 sSrc2
[0626] SORR sDest sSrc1 sSrc2
[0627] SXOR sDest sSrc1 sSrc2
[0628] SLSL sDest sSrc1 sSrc2
[0629] SLSR sDest sSrc1 sSrc2
```

Stores result of various operations between slot values into destination slot.

- `SADD` stores `sSrc1 + sSrc2` in `sDest`.
- `SSUB` stores `sSrc1 - sSrc2` in `sDest`.
- `SMUL` stores `sSrc1 * sSrc2` in `sDest`.
- `SDIV` stores `sSrc1 / sSrc2` in `sDest`.
- `SMOD` stores `sSrc1 % sSrc2` in `sDest`.
- `SAND` stores `sSrc1 & sSrc2` in `sDest`.
- `SORR` stores `sSrc1 | sSrc2` in `sDest`.
- `SXOR` stores `sSrc1 ^ sSrc2` in `sDest`.
- `SLSL` stores `sSrc1 << sSrc2` in `sDest`.
- `SLSR` stores `sSrc1 >> sSrc2` in `sDest`.

Having destination as `s0` has no effect (it will be reset to 0 before the next code is handled).

All operations are done as if those were C expressions with `int`s as operands, which notably means that:

- All numbers are signed.
- Divisions round towards 0 (as opposed to down).
- Right shift is an arithmetic shift, which means that the msb aka "sign bit" will be repeated however many bits the value has been shifted (as opposed to having the extra bits filled with 0).

_**Note**: Vanilla events use `SADD sDst sSrc s0` to move the value of a slot into another._

---

</details>

<details>
<summary>07 : queue operations (SENQUEUE, SDEQUEUE)</summary>

```
[0720] SENQUEUE Slot
[0721] SENQUEUE
[0722] SDEQUEUE Slot
```

- `SENQUEUE` enqueues the value of the given slot. The parameterless variant enqueues the value of `s1`.
- `SDEQUEUE` dequeues the value in the front of the queue into the given slot.

See also the section on the event queue in `Generalities`.

---

</details>

<details>
<summary>08 : label (LABEL)</summary>

```
[0820] LABEL Identifier
```

Marks the location of a label, which is a possible target for jump codes. This code does nothing by itself.

Label lookup is done by looking for each event code from the *start* of the current scene and getting the first matching label code. Do note that only labels with the standard size of `2` will be consided for the search.

Note that the lookup doesn't check for ends and whatnot. You could very well get the game into an endless loop if you look for a label that doesn't exist! (That or jump into a completely unrelated scene which may have interesting effects).

Label identifiers are 2 bytes and can range from 0 to `$FFFF`. There is no technical requirements when it comes to identifying labels other than that.

---

</details>

<details>
<summary>09 : jump to label (GOTO) </summary>

```
[0920] GOTO Identifier
```

Jump to identified label unconditionally. For more information on how label lookup is done, see `08 : label (LABEL)`.

---

</details>

<details>
<summary>0A : call subscene (CALL)</summary>

```
[0A40] CALL TargetOffset
```

Calls the scene at given address. A "call" is done by pushing current event scene start/cursor on the event call stack and jumping to the given offset. When the called scene reaches an `ENDA` (unless specific conditions are met, see `01 : end` for details), then the pushed scene start/cursor will be restored, effectively given control back to the calling scene.

The event call stack has room for 8 start/cursor pairs.

If the target scene address is negative, the target event scene address will be read from `s2`. EA standard raws provide the parameterless `TUTORIAL_CALL` that handles just that (EA doesn't support negative "offset" values, so if you need to call a scene from a pointer in a slot using this is required).

---

</details>

<details>
<summary>0B : enqueue event engine invocation (TODO: figure out)</summary>

```
[0B40] -
[0B41] -
```

TODO: add to experimental

- `[0B40]` equeues an event engine invocation. This means that the target event scene will be called *after the current event scene ends*. If other event engine invocations are already queued, this will be put at the end of the queue (because it's a queue).
- `[0B41]` does tutorial event stuff, TODO: need to investigate further.

If TargetOffset is negative, the target event scene address will be read from `s2`.

---

</details>

<details>
<summary>0C : conditional jump to label (BEQ, BNE, BGE, BGT, BLE, BLT)</summary>

```
[0C40] BEQ Identifier Slot1 Slot2
[0C40] BNE Identifier Slot1 Slot2
[0C40] BGE Identifier Slot1 Slot2
[0C40] BGT Identifier Slot1 Slot2
[0C40] BLE Identifier Slot1 Slot2
[0C40] BLT Identifier Slot1 Slot2
```

- `BEQ` jumps to the identified label if `Slot1 == Slot2`.
- `BNE` jumps to the identified label if `Slot1 != Slot2`.
- `BGE` jumps to the identified label if `Slot1 >= Slot2`.
- `BGT` jumps to the identified label if `Slot1 > Slot2`.
- `BLE` jumps to the identified label if `Slot1 <= Slot2`.
- `BLT` jumps to the identified label if `Slot1 < Slot2`.

For more information on how label lookup is done, see `08 : label (LABEL)`.

Comparisons are done as if those were C expressions with `int` operands. Which means numbers in slots are to be considered signed.

---

</details>

<details>
<summary>0D : call native function (ASMC)</summary>

```
[0D40] ASMC FuncOffset
```

Calls native ("asm") function.

The called function will be given one argument: the pointer to the running event engine [proc](https://feuniverse.us/t/guide-doc-asm-procs-or-6cs-coroutines-threads-fibers-funky-structs-whatever/3352?u=stanh). This is useful if you need to make something that will *pause* the execution of the event engine until it is done (typically some cosmetic effect). The return value of the called function is ignored.

In C terms, this means function pointer has the following signature:

```c
void(*)(struct EventEngineProc*);
```

The `ASMC` code will *always* stop the event engine execution for the current frame. This means that every time you use `ASMC`, no matter what function you call, you will always "loose" at least one frame.

There is no way of reading the function address from a slot. `ASMC` won't do anything if the function pointer is 0.

---

</details>

<details>
<summary>0E : sleep/pause/stall (STAL, STAL2, STAL3) </summary>

```
[0E20] STAL Duration
[0E21] - Duration
[0E22] STAL2 Duration
[0E23] STAL3 Duration
```

- `STAL` will pause the scene for the given duration.
- `[0E21]` will pause the scene for the given duration. The pause will end early if evbit 3 (text-skipping) is set, or B is pressed at any point.
- `STAL2` will pause the scene for the given duration. If either the "fast game speed" option is set or the A button is held, then the "counting down" will be 4 times faster.
- `STAL3` combines the behavior of `[0E21]` and `STAL2`.

No sleeping will occur if events are currently being skipped (evbit 2 set).

There is no way of getting the duration from an event slot. If Duration is 0, the game will hang.

---

</details>

<details>
<summary>0F : counter operations (COUNTER_CHECK, COUNTER_SET, COUNTER_INC, COUNTER_DEC)</summary>

```
[0F20] COUNTER_CHECK Identifier
[0F21] COUNTER_SET Identifier Value
[0F22] COUNTER_INC Identifier
[0F23] COUNTER_DEC Identifier
```

- `COUNTER_CHECK` gets value of counter into `sC`.
- `COUNTER_SET` sets counter to given value. You cannot get this value from a slot.
- `COUNTER_INC` increments value of given counter by 1.
- `COUNTER_DEC` decrements value of given counter by 1.

See also the section on counters in `Generalities`.

`COUNTER_INC` and `COUNTER_DEC` will not allow the counter value to overflow or underflow. If the value is 0 and `COUNTER_DEC` is used, the value will still be 0. If the value is 15 and `COUNTER_INC` is used, the value will still be 15.

_**Note**: EA standard raws have provided `COUNTER_ADD` and `COUNTER_SUBSTRACT` for a while. Those do not work as advertised: They are simple increments/decrements. `COUNTER_INC` and `COUNTER_DEC` in experimental raws are aliases to those without defining the extra unused argument._

---

</details>

<details>
<summary>10 : configure skipping (EVBIT_MODIFY)</summary>

```
[1020] EVBIT_MODIFY Configuration
```

This will configure what the player is allowed to skip during a scene. This simply sets the according evbits with some additional bookkeeping.

Here's the list of allowed configuration identifiers:

- `0` allows scene skipping, dialogue skipping and dialogue fast-forwarding.
- `1` disallows scene skipping, dialogue skipping and dialogue fast-forwarding.
- `2` allows scene skipping and dialogue skipping, but disallows dialogue fast-forwarding.
- `3` disallows scene skipping, but allows dialogue skipping and dialogue fast-forwarding.
- `4` disallows scene skipping and dialogue skipping, but allows dialogue fast-forwarding.

Any configuration that isn't in this list will have the game hang.

If the configuration is nonzero, and if the player is currently skipping the scene, the "skipping" evbit (evbit 2) will be cleared and the "faded in" evbit (evbit 8) will be set.

There is no way of getting the configuration from an event slot.

_**Note**: "scene skipping" refers to pressing start to skip a scene. "dialogue skipping" refers to pressing B or start to skip a dialogue. "dialogue fast-forwarding" refers to pressing A, B or any D-pad direction to have the current text box content display entirely immediately._

---

</details>

<details>
<summary>11 : set ignored key presses (STORETOSOMETHING)</summary>

```
[1120] STORETOSOMETHING Mask
```

TODO: add better alias to experimental stdlib.

Sets global key press ignore mask. `Mask` is a bitset where each bit maps to a button of the GBA console. When a bit is set, then the corresponding button will be ignored for all purposes but the soft-reset sequence.

bit-to-button map:

	bit 0 | A button
	bit 1 | B button
	bit 2 | select button
	bit 3 | start button
	bit 4 | right D-pad button
	bit 5 | left D-pad button
	bit 6 | up D-pad button
	bit 7 | down D-pad button
	bit 8 | R button
	bit 9 | L button

You can use the EA `1100001100b` notation (`b` suffix) to make it easier to visualize in your source (this example would ignore buttons select, start, R and L).

---

</details>

<details>
<summary>12 : smooth BGM start/change (MUSC)</summary>

```
[1220] MUSC SongId @  identied by SongId
```

Transitions BGM to given song. A song id of `0x7FFF` (`INT16_MAX`) is silent.

This code stops the event engine for a single frame, but then the scene continues to be executed while the transition is occuring (no further waiting occurs).

If SongId is negative, then the song id will be read from `s2`.

---

</details>

<details>
<summary>13 : BGM start/change (MUSCFAST, MUSCMID, MUSCSLOW)</summary>

```
[1322] MUSCFAST SongId
[1324] MUSCMID SongId
[1326] MUSCSLOW SongId
```

Stops current BGM song if any, and transitions to new BGM song. A song id of `0x7FFF` (`INT16_MAX`) is silent.

- If the new BGM song is not silent, then the old BGM will be stopped immediately (no transition). If the scene is being skipped, no song switch occurs.
- If the new BGM is sient, then the old BGM will properly transitionned towards silence (unless the scene is being skipped, in which case the transition is instant).

It is the *subcode* that dictates which speed to fade the new BGM volume in. The lower the faster. As you can see above, MUSCFAST has subcode 2, MUSCMID has subcode 4 and MUSCSLOW has subcode 6. For reference, the transition speed of `[1220] MUSC` is 3.

This code stops the event engine for a single frame, but then the scene continues to be executed while the transition is occuring (no further waiting occurs).

If SongId is negative, then the song id will be read from `s2`.

---

</details>

<details>
<summary>14 : BGM overwrite (MUSS, MURE)</summary>

```
[1420] MUSS SongId
[1421] MURE Speed
```

- `MUSS` transitions BGM to given song. The previously playing BGM song is remembered.
- `MURE` transitions BGM back to remembered song at given speed. Lower "speed" means faster transition.

You can only "remember" one song. If you stack MUSSes, then only the *last* overwritten song will be "remembered". TODO: verify.

This code stops the event engine for a single frame, but then the scene continues to be executed while the transition is occuring (no further waiting occurs).

For `MUSS`, if song id is negative, then the song id will be read from `s2`. For `MURE`, there is no way of getting speed from a slot.

---

</details>

<details>
<summary>15 : make/unmake BGM quieter (MUSI, MUNO)</summary>

```
[1520] MUSI
[1521] MUNO
```

- `MUSI` transitions BGM volume down. Does nothing if scene-skipping (evbit 2 set).
- `MUNI` transitions BGM volume back to normal after `MUSI`. Transition is instant if scene-skipping (evbit 2 set).

This code stops the event engine for a single frame, but then the scene continues to be executed while the transition is occuring (no further waiting occurs).

---

</details>

<details>
<summary>16 : play arbitrary song (SOUN)</summary>

```
[1620] SOUN SongId
```

Plays identified song. Only plays song if scene is not being skipped, dialogue is not being skipped and the "sound effect" player option is set.

This code doesn't stops the event engine (no waiting occurs).

If SongId is negative, the song id is read from `s2`.

---

</details>

<details>
<summary>17 : fade in/out (FADU, FADI, FAWU, FAWI)</summary>

```
[1720] FADU Speed
[1721] FADI Speed
[1722] FAWU Speed
[1723] FAWI Speed
```

- `FADU` fades o**U**t of **D**ark. Clears evbit 8.
- `FADI` fades **I**nto **D**ark. Sets evbit 8.
- `FAWU` fades o**U**t of **W**hite. Clears evbit 8.
- `FAWI` fades **I**nto **W**hite. Sets evbit 8.

Hopefully it being said like that can make for decent mnemonics?

No fade happens if the scene is being skipped. The event engine will wait for the fade to end before continuing.

---

</details>

<details>
<summary>18 : arbitrary color effect (STARTFADE, ENDFADE, FADECOLORS)</summary>

```
[1860] STARTFADE
[1861] ENDFADE
[1862] FADECOLORS Target Speed Red Green Blue
```

TODO: figure more out

`STARTFADE` sets up the fade buffer from current palette.

`Target` is a pair of bytes: the first byte is the index of the first targetted palette, the second byte is the number of targetted palettes.

If scene-skipping or faded in, then `FADECOLORS` is instant.

---

</details>

<details>
<summary>19 : CHECK_[MODE|CHAPTER_NUMBER|HARD|TURNS|ENEMIES|OTHERS|SKIRMISH|TUTORIAL|MONEY|EVENTID|POSTGAME]</summary>

```
[1920] CHECK_MODE
[1921] CHECK_CHAPTER_NUMBER
[1922] CHECK_HARD
[1923] CHECK_TURNS
[1924] CHECK_ENEMIES
[1925] CHECK_OTHERS
[1926] CHECK_SKIRMISH
[1927] CHECK_TUTORIAL
[1928] CHECK_MONEY
[1929] CHECK_EVENTID
[192A] CHECK_POSTGAME
```

Get various information in `sC`.

- `CHECK_MODE` gets current mode identifier: 0 for "prologue" chapters, 1 for eirika route, 2 for ephraim route.
- `CHECK_CHAPTER_NUMBER` gets current chapter id. Cares for `LOMA`.
- `CHECK_HARD` gets 1 if the player is playing on difficult, 0 otherwise.
- `CHECK_TURNS` gets the current turn number as it would be displayed in the status screen. Turn changes occur between the green and blue phases.
- `CHECK_ENEMIES` gets the number of alive red units.
- `CHECK_OTHERS` gets the number of alive green units.
- `CHECK_SKIRMISH` gets 0 for story chapters, 1 for tower/ruins and 2 for skirmishes.
- `CHECK_TUTORIAL` gets 1 if the player is playing on easy, 0 otherwise.
- `CHECK_MONEY` gets the party gold amount. It gets 0 on chapter 5x.
- `CHECK_EVENTID` gets eid identifier linked to running event. That eid is what is specified in the "condition code" of the event (the `TURN`, `AFEV`, `CHAR`... that had this scene called). Gets 0 for scenes called otherwise.
- `CHECK_POSTGAME` gets 1 if the player reached postgame, 0 otherwise.

---

</details>

<details>
<summary>1A : set text type (TEXTSTART, REMOVEPORTRAITS, ...)</summary>

```
[1A20] TEXTSTART
[1A21] REMOVEPORTRAITS
[1A22] _0x1A22
[1A23] TUTORIALTEXTBOXSTART
[1A24] SOLOTEXTBOXSTART
[1A25] _0x1A25
```

TODO: add better aliases to experimental stdlib.

Sets active text type according to subcode. The text type is what dictates how codes such as `TEXTSHOW` or `BACG` behave.

- `TEXTSTART` sets text type 0, which is background-less regular dialogue.
- `REMOVEPORTRAITS` sets text type 1, which is regular dialogue with background.
- `_1A22` sets text type 2, which is CG with text (only cg background available is the lyon + twins one).
- `TUTORIALTEXTBOXSTART` sets text type 3, which is displaying text in the yellow box thing
- `SOLOTEXTBOXSTART` sets text type 4, which is displaying text in a single regular dialogue box
- `_0x1A25` sets text type 5, which is also displaying in the yellow box thing... but slightly differently? TODO: investigate

If the new text type is different from the previously active text type, this will end text interpreters and clear text and portraits. This notably means you can't use the `[Events]`/`TEXTCONT` text code to switch from one text type to another mid-dialogue (you'd need to use two different text entries to have this effect).

---

</details>

<details>
<summary>1B : display text (TEXTSHOW, TEXTSHOW2, REMA)</summary>

```
[1B20] TEXTSHOW TextId
[1B21] TEXTSHOW2 TextId
[1B22] REMA
```

`TEXTSHOW` and `TEXTSHOW2` display text according to the active text type.

- `TEXTSHOW` resets the "text-skipping" evbit (evbit `3`) before displaying text.
- `TEXTSHOW2` will only display text if the "text-skipping" evbit (evbit `3`) isn't set.

If TextId is negative, the displayed text id will be read from `s2`. If the displayed text id is zero, nothing happens.

`REMA` clears most text-related things. More precisely, it ends any active text interpreter, clears text, removes portraits and clears the "text-skipping" evbit (evbit `3`).

---

</details>

<details>
<summary>1C : continue text (TEXTCONT)</summary>

```
[1C20] TEXTCONT
```

Continues displaying current text after it has returned control to the event engine through the `[Events]` text code.

If the "scene-skipping" evbit (evbit `2`) is set, this has the same effect as `[1B22] REMA` except for clearing the "text-skipping" evbit (evbit `3`).

---

</details>

<details>
<summary>1D : wait for text (TEXTEND)</summary>

```
[1D20] TEXTEND
```

Waits for either the text to reach the end (`[X]`) or for it to temporarily return control (`[Events]`). In the latter case, use `[1C20] TEXTCONT` to resume text where it left off.

`TEXTEND` will set `sC` to the result id of any prompt within text (ex: for Yes/No the possible results will be 1/2). If the text was skipped, `sC` will be 0. It may be a good idea to prevent text-skipping and scene-skipping before displaying a text with an important prompt (see `10 : configure skipping`).

If the "scene-skipping" evbit (evbit `2`) is set, this has the same effect as `[1B22] REMA` except for clearing the "text-skipping" evbit (evbit `3`). It will also set `sC` to 0.

---

</details>

<details>
<summary>1E : display portraits (TODO)</summary>

```
[1E20] - FaceId
[1E21] - FaceId
[1E22] - FaceId
[1E23] - FaceId
[1E24] - FaceId
[1E25] - FaceId
[1E26] - FaceId
[1E27] - FaceId
```

TODO: add to experimental stdlib.

Puts a portrait on the portrait slot given by the subcode. Internally, it just executes the `[Open{FaceSlot}][LoadFace][FaceId][1]` (or `[Open{FaceSlot}][ClearFace]` when FadeId is `-2`) text codes.

- `[1E20]` puts face on slot `0` ("far left").
- `[1E21]` puts face on slot `1` ("mid left").
- `[1E22]` puts face on slot `2` ("left").
- `[1E23]` puts face on slot `3` ("right").
- `[1E24]` puts face on slot `4` ("mid right").
- `[1E25]` puts face on slot `5` ("far right").
- `[1E26]` puts face on slot `6` ("far far left").
- `[1E27]` puts face on slot `7` ("far far right").

If FaceId is `-1`, then the effective face id is read from `s2`.

If FaceId is `-2`, it has the same effect as calling `[ClearFace]` for the slot corresponding to the code. It will also clear any opened text box.

If FaceId is `-3`, all faces are cleared (reguardless of the code used).

This code doesn't wait for the face displaying/clearing transition effect is done before giving control back to the event engine. Be careful as using those and then displaying text immediately after may have interesting side effects (as there would be two dialogue engines running simultaneously). Use `STAL` if needed.

---

</details>

<details>
<summary>1F : move portraits (TODO)</summary>

```
[1F20] - From To
```

TODO: add to experimental stdlib.

Moves portrait on the `From` slot to the `To` slot (see `1E : display portraits` for how portait slots are identified). Internally, it just executes the `[Open{From}][Move{To}]` text codes.

This code doesn't wait for the face moving transition effect is done before giving control back to the event engine. Be careful as using those and then displaying text immediately after may have interesting side effects (as there would be two dialogue engines running simultaneously). Use `STAL` if needed.

---

</details>

<details>
<summary>20 : clear text boxes (TODO)</summary>

```
[2020] -
```

TODO: add to experimental stdlib.

Clears any open text box.

---

</details>

<details>
<summary>21 : display text background (BACG, ...)</summary>

```
[2140] BACG BackgroundId
[2141] _0x2141 BackgroundId TargetTextType Speed
[2142] - BackgroundId SourceColor Speed
[2143] - TargetColor Speed
```

TODO: add better aliases and more to experimental stdlib.

- `BACG` displays given background for the active text type, without transition.
- `_0x2141` will start a transition from the current background to a new background as if it was displayed for the given text type. This code doesn't switch text types after the transition, you will have to do it yourself.
  - You are not allowed to transition from a non-background text type to another non-background text type (the game will hang).
  - You *are* allowed to transition from a baground text type to a non-background text type, in which case the background id is ignored and the currently displayed background will be faded out.
- `[2142]` displays given background for active text type, and fades it in from the given color.
- `[2143]` fades the currently displayed background to the given color.

_**Note**: due to what I assume is a bug in the engine, the only background that can be displayed for text type 2 ("cg text") is the lyon/eirika/ephraim being happy scene thing._

_**Note**: Only text types 1 ("dialogue with background") and 2 ("cg text") support displaying backgrounds. If you try to display backgrounds for any other text type, the game will hang._

---

</details>

<details>
<summary>22 : clear screen (CLEAN)</summary>

```
[2220] CLEAN
```

Clears bg0 and bg1, text, portraits, reloads default font, default map sprite palettes, ui graphics, and unblocks game graphics if they were blocked.

---

</details>

<details>
<summary>23 : disable battle map display (TODO)</summary>

```
[2320] -
```

Manually disables battle map display and sets evbit `12`. This can be implicetely called by text codes for text types involving backgrounds.

More speficically, this disables map sprite display, weather effects and camera updates.

---

</details>

<details>
<summary>24 : restore battle map display (TODO)</summary>

```
[2420] -
```

Restores battle map display after `[2320]`. This can be implicitely called by text codes for text types involving backgrounds.

If evbit `12` isn't set, does nothing.

---

</details>

<details>
<summary>25 : load chapter map (LOMA)</summary>

```
[2520] LOMA ChapterId
```

Loads new map given chapter id and sets camera given position in `sB`.

The chapter number *will* be updated, so be careful! This means that after the current scene has ended, if you didn't restore the chapter via another `LOMA`, the chapter will executed as if it were the loaded chapter, not the original!

If given chapter id is negative, will load chapter id from `s2`.

---

</details>

<details>
<summary>26 : camera control (CAMERA, CAMERA2)</summary>

```
[2620] CAMERA [X, Y]
[2621] CAMERA CharId
[2628] CAMERA2 [X, Y]
[2629] CAMERA2 CharId
```

Moves the camera given coordinates. For variants taking units, will move given the unit's position.

- `CAMERA` moves the camera in such a way that the given position is on screen, and more than 2 tiles away from the edge (if possible).
- `CAMERA2` moves the camera in such a way that the given position becomes the center of the screen. Due to a bug in the vanilla engine, this can move the camera in such a way that part of "past the edge of the map" junk is visible, so be careful!

For variants taking coordinates, if both coordinates are negatve then the target position will be read from `sB`. Experimental raws provide `CAMERA_SB` and `CAMERA2_SB` for convenience.

_**Note**: "old" EA standard raws only provide `CAM1`, which is an alias for `CAMERA` for character variants, but for `CAMERA2` for position variants!_

---

</details>
