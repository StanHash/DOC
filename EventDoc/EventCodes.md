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

### Eids / Flags

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
- evbit `11` is the "changing game mode" evbit. When set, ending the event engine will also end the active battle map, allowing the `GAMECTRL` proc to continue its flow and change game mode.
- evbit `12` is the "gfx locked" evbit. It is automatically set and unset by the "lock/unlock gfx" event codes.

evbits persist for the duration of a scene.

### Unit parameters

Most codes that work with units take character identifiers as parameters. There are some common rules this kind of parameter follow almost all of those codes follow (the only exception is TODO):

- When the argument is `0`, the unit taken into account is the player leader unit.
- When the argument is `-1`, the unit taken into account is the active unit.
- When the argument is `-2`, the unit taken into account is the unit at position in `sB`.
- When the argument is `-3`, the unit taken into account is the first unit whose character id corresponds to `s2`.
- Otherwise, the unit taken into account is the first unit whone character id corresponds to the argument.

Each time I name a code paramter `CharId`, assume that those rules apply unless otherwise noted.

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

- `CHECK_EVBIT` gets evbit state in `sC`.
- `CHECK_EVENTID` gets eid state in `sC`.

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

**Note**: The code parameter is in fact the **speed** of the fade (not its duration!). A larger value will have the fade be shorter and vice-versa.

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

Camera movement is instant if scene-skipping (evbit 2 set) or faded in (evbit 8 set). Otherwise, the event engine waits for the camera movement to complete before continuing the scene.

_**Note**: "old" EA standard raws only provide `CAM1`, which is an alias for `CAMERA` for character variants, but for `CAMERA2` for position variants!_

---

</details>

<details>
<summary>27 : apply/remove tile changes (TILECHANGE, TILEREVERT)</summary>

```
[2720] TILECHANGE Id
[2721] TILEREVERT Id
```

- `TILECHANGE` applies a tile change if not already applied.
- `TILEREVERT` reverts a tile change unless it wasn't applied.

If given id is `-1`/`0xFFFF`, a position is read from `sB`. The target tile change will be the first in the current map's tile change list for which its area overlap with that position.

If given id is `-2`/`0xFFFE`, it will look for the tile change the same way as for `-1`/`0xFFFF`, but for the position of the active unit.

If give id is `-3`/`0xFFFD`, mutiple tile changes will be applied/reverted. It will read all tile change ids from the event queue.

Tile change is instant if faded in (evbit 8 set). Otherwise, the event engine waits for the tile change fade effect to complete before continuing the scene.

---

</details>

<details>
<summary>28 : set weather (WEA1)</summary>

```
[2820] WEA1 WeatherId
```

Sets active weather.

For reference, here's a list of valid weather identifiers:

- `0` is no weather.
- `1` is snowing.
- `2` is snowstorm.
- `3` is something blue.
- `4` is rain.
- `5` is flames.
- `6` is sandstorm.
- `7` is background clouds.

_**Note**: Interestingly enough, EA standard raws define `WEA1` as code `2821`, which suggests that this is also what the vanilla game uses. The difference in subcode doesn't matter for this code in particular but it is nonetheless notable._

---

</details>

<details>
<summary>29 : set fog vision (VCWF)</summary>

```
[2920] VCWF Vision
```

Sets active fog vision range.

A vision range of 0 means no fog. A negative vision range loads the chapter's default fog vision.

If not scene-skipping, the event engine will wait for the displayed transition to end before continuing the scene.

---

</details>

<details>
<summary>2A : move to chapter (MNTS, MNCH, MNC2, MNC3, MNC4)</summary>

```
[2A20] MNTS <Ignored>
[2A21] MNCH ChapterId
[2A22] MNC2 ChapterId
[2A23] MNC3 ChapterId
[2A24] MNC4 <Ignored>
```

TODO: add better aliases to experimental.

- `MNTS` has the game go to the title screen.
- `MNCH` has the game go to the world map, running the identified chapter's world map unlock events.
- `MNC2` has the game go to the identified chapter, without going through the world map.
- `MNC3` has the game go to the identified chapter immediately, without event going through the save screen.
- `MNC4` has the game go to the game ending and credits.

All variants but `MNC3` set evbit 11. All variants set evbit 10. All variants start a BGM fade out.

If `ChapterId` is negative, the target chapter id will be read from `s2`.

_**Note**: be careful when using `MNC2` (and `MNC3`)! If you move to a chapter with a world map location attached to it, that location won't have been marked as the next "story" location (this is typically done through the chapter's world map unlock events). In other words, the next chapter will probably be considered as a skirmish!_

---

</details>

<details>
<summary>2B : configure next unit load (TODO)</summary>

```
[2B20] - UnitCount
[2B21] - Chance
[2B22] -
```

This is primarily used in the vanilla game to gain more control on loading units for dungeons (tower/ruins).

- `[2B20]` sets the number of units to load for the next load. A value of 0 (which is default) means that it will load up until the terminating unit (any unit definition with char id 0).
- `[2B21]` sets the chance (in percent) for units that are marked to be loaded at a random position to actually be loaded at a random position (More precisely, it sets the proportion of units in the load group to be loaded as such).
- `[2B22]` disables REDAs for the next load.

For `[2B20]` and `[2B21]`, if the argument is negative, it will be read from `s2`.

---

</details>

<details>
<summary>2C : load units (LOAD1, LOAD2, LOAD3, LOAD4)</summary>

```
[2C40] LOAD1 RestrictionType UnitsOffset
[2C41] LOAD2 <Unused> UnitsOffset
[2C42] LOAD3 RestrictionType UnitsOffset
[2C43] LOAD4 RestrictionType <Unused>
```

TODO: add better aliases to experimental.

- `LOAD1` loads unit group respecting restriction (see below).
- `LOAD2` loads unit group respecting restriction `2` (see below).
- `LOAD3` loads unit group respecting restriction (see below). The units in the group will be replaced by the corresponding units in the player's deployed unit list.
- `LOAD4` loads the current skirmish enemy group respecting restriction.

A "restriction" identifies additional conditions that have to be met for loading *player* units. This is a list of valid identifiers and what they mean:

- `0` means to not load dead units.
- `1` means no special restrictions.
- `2` means to not load dead units unless they are one of Seth, L'Arachel, Myrrh and Innes. Units loaded with restriction 2 will also be considered as "cutscene units" and will be removed when the scene ends (even non-player units!).

In addition to that, an *enemy* unit won't be loaded if its target position is occupied by another unit and it doesn't have a REDA assigned to it (or it has been marked to load at a random position). (Player and NPC units will have their position adjusted).

Units with defined initial movement (aka `REDA`s) will have their initial movement displayed. It may be wise to use an `ENUN` after loading units to avoid conflicting events (or you could not do that and instead opt to abuse this for dramatic camera movement or something, but stay careful!).

Not all units in an unit group will necessarily be loaded simultaneously: if more than 4 units require displayed movement simultaneously, the event engine will wait for a moving unit to reach its destination before continuing to load.

If scene-skipping (evbit 2 set) or faded in (evbit 8 set), unit load is instant and no movement is displayed.

For `LOAD1`, `LOAD2` and `LOAD3`, if the unit group address is negative, the effective address will be read from `s2`. EA standard raws provide `LOAD_SLOT1` which is bad but the only way to make use of this because EA doesn't all for negative offsets. TODO: add `LOAD_S2`, `LOAD_CUTSCENE_S2`, `LOAD_DEPLOYED_S2`.

TODO: maybe document unit groups.

---

</details>

<details>
<summary>2D : override map sprite palettes (TODO)</summary>

```
[2D20] - BlueId RedId GreenId
```

TODO: add to experimental

Overwrites standard map sprite palettes with palettes identified as such:

- `0` for default (unchanged) palette.
- `1` for blue palette.
- `2` for red palette.
- `3` for green palette.
- `4` for sepia flashback palette.

This isn't reset at the end of a scene! So make sure you do it yourself if needed. (It will not persist during gameplay tho, anything that reloads palettes will cancel this effect).

---

</details>

<details>
<summary>2E : get character id (CHECK_ACTIVE, CHECK_AT)</summary>

```
[2E20] CHECK_AT [X, Y]
[2E21] CHECK_ACTIVE
```

- `CHECK_AT` gets the character id of the unit at given position. (0 if there is no unit there).
- `CHECK_ACTIVE` gets the character id of the current active unit. (0 if there is currently no active unit).

For `CHECK_AT`, there is no way of reading the effective position from a slot.

---

</details>

<details>
<summary>2F : move unit (MOVE, MOVEONTO, MOVE_1STEP, MOVEFORCED)</summary>

```
[2F40] MOVE Speed CharId [X, Y]
[2F41] MOVEONTO Speed CharId TargetCharId
[2F42] MOVE_1STEP Speed CharId Direction
[2F43] MOVEFORCED <Unused> CharId <Unused>
```

TODO: better `MOVEFORCED` to experimental.

Moves the unit identified through `CharId`.

- `MOVE` moves the unit to the given coordinates.
- `MOVEONTO` moves the unit to where the target unit is located. The `TargetCharId` doesn't follow the usual rules for unit parameters (it only looks for a unit with that character id).
- `MOVE_1STEP` moves the unit one step in the given direction.
- `MOVEFORCED` moves the unit given the defined movement in the event queue. Defined movement follow the exact same format as `REDA`s.

For non-`MOVEFORCED` variants, if speed is negative, movement is done instantly and isn't displayed. Otherwise it dicates the speed at which the unit is moving (0 means default). TODO: investigate speed more.

If scene-skipping (evbit 2 set), movement is instant reguardless of the speed argument. Note that `MOVEFORCED` may not work properly when scene-skipping. (TODO: investigate).

Valid directions for `MOVE_1STEP` are:

- `0` for left.
- `1` for right.
- `2` for down.
- `3` for up.

If displayed unit movement cannot start (because too many units on the map are already moving), the event engine will wait for a moving unit to reach its destination before moving this unit.

The event engine doesn't wait for displayed movement to end before continuing.

---

</details>

<details>
<summary>30 : wait for displayed movement (ENUN)</summary>

```
[3020] ENUN
```

Stops the event engine until all displayed unit movement have ended.

If scene-skipping (evbit 2 set), will forcefully end all displayed movement immediately.

---

</details>

<details>
<summary>31 : display move/effect range (SHOW_ATTACK_RANGE, HIDE_ATTACK_RANGE)</summary>

```
[3120] SHOW_ATTACK_RANGE CharId
[3121] HIDE_ATTACK_RANGE
```

- `SHOW_ATTACK_RANGE` displays the given units's move+attack range (or move+staff range if that unit doesn't have usable weapons).
- `HIDE_ATTACK_RANGE` hides any displayed range.

`SHOW_ATTACK_RANGE` changes the active unit to the unit whose range is displayed. `HIDE_ATTACK_RANGE` restores it to the unit it was beforehand.

If scene-skipping (evbit 2 set), nothing happens.

---

</details>

<details>
<summary>32 : load single unit (SPAWN_xyz)</summary>

```
[3240] SPAWN_ALLY CharId [X, Y]
[3241] SPAWN_NPC CharId [X, Y]
[3242] SPAWN_ENEMY CharId [X, Y]
[324F] SPAWN_CUTSCENE_ALLY CharId [X, Y]
```

Loads a single unit give character id and target position.

The unit's class will be the character's default. The character's stats and level will be the character's bases. The loaded units won't start with any items, with null AI **and with the "drop item" state set**.

If `CharId` is `-3`/`0xFFFD`, the loaded character id is read from `s2`.

If X and Y are negative, the target position is read from `sB`.

`SPAWN_CUTSCENE_ALLY` loads a "cutscene unit" in very much the any `2C : load units` with restriction `2` would.

---

</details>

<details>
<summary>33 : check unit state (CHECK_xyz)</summary>

```
[3320] CHECK_EXISTS CharId
[3321] CHECK_STATUS CharId
[3322] CHECK_ALIVE CharId
[3323] CHECK_DEPLOYED CharId
[3324] CHECK_ACTIVEID CharId
[3325] CHECK_ALLEGIANCE CharId
[3326] CHECK_COORDS CharId
[3327] CHECK_CLASS CharId
[3328] CHECK_LUCK CharId
```

Gets various informations reguarding a given [unit](#unit-parameters) in `sC`.

- `CHECK_EXISTS` gets `1` if a matching unit exists, `0` otherwise.
- `CHECK_STATUS` gets byte at `+0x30` in matching unit's character entry. This may be bugged.
- `CHECK_ALIVE` gets `1` if matching unit exists and is alive, `0` otherwise.
- `CHECK_DEPLOYED` gets `1` if matching unit is deployed, `0` otherwise.
- `CHECK_ACTIVEID` gets `1` if `CharId` corresponds to the character id of the active unit.
- `CHECK_ALLEGIANCE` gets `2` if matching unit is red, `0` if it's blue and `1` if it's either green or purple.
- `CHECK_COORDS` gets the matching units position (in the form of a pair of halfwords, suitable for most purposes involving coords).
- `CHECK_CLASS` gets the matching units class id.
- `CHECK_LUCK` gets the matching units luck stat (with taking bonuses into account).

**Note**: `CHECK_EXISTS` and `CHECK_ALIVE` are the only members of the `33` code family that will not hang when no matching unit exist. All others will (even `CHECK_ACTIVEID`, which doesn't otherwise care for the matching unit).

---

</details>

<details>
<summary>34 : modify unit state (REMU, REVEAL, CUSx, SET_HP, ...)</summary>

```
[3420] REMU CharId
[3421] REVEAL CharId
[3422] CUSA CharId
[3423] CUSN CharId
[3424] CUSE CharId
[3425] SET_HP CharId
[3426] SET_ENDTURN CharId
[3427] _0x3427 CharId
[3428] SET_STATE CharId
[3429] - CharId
[342A] CLEA <Unused>
[342B] CLEN <Unused>
[342C] CLEE <Unused>
[342D] SET_SOMETHING CharId
[342E] DISA_IF CharId
[342F] DISA CharId
```

TODO: better code names, as usual.

Modify various [unit](#unit-parameters) states.

- `REMU` removes matching unit from the player party. Note that this doesn't actually remove the unit itself, just hides it.
- `REVEAL` reverts the effect of a previous `REMU`.
- `CUSA` changes the matching units faction to blue.
- `CUSN` changes the matching units faction to green.
- `CUSE` changes the matching units faction to red.
- `SET_HP` sets the matching units HP to the value in `s1`. If HP is set to 0, also marks that unit as dead.
- `SET_ENDTURN` grays out the matching unit.
- `_0x3427` marks the matching unit as having being moved by the AI during this phase. Note: unsure, investigate.
- `SET_STATE` deploys or undeploys matching unit given value in `s1`: `1` will deploy the unit, `0` will undeploy the unit, and `-1` will deploy or undeploy the unit based on units state bit 21 (?).
- `[3429]` does nothing.
- `CLEA` hides every blue unit, and then clears all cutscene units.
- `CLEN` removes all green units.
- `CLEE` removes all red units.
- `SET_SOMETHING` starts the death fade map animation for matching units map sprite.
- `DISA_IF` waits for any death fade map animation to end before permanently removing matching unit.
- `DISA` permanently removes matching unit.

**Note**: `REMU` through `[3429]` will hang if no matching unit exist, `CLEA` through `CLEE` don't care, and `SET_SOMETHING` through `DISA` will silently do nothing.

---

</details>

<details>
<summary>35 : change unit class (RECLASS, RECLASS_FROMCHAR, SWITCH_CLASSES)</summary>

```
[3540] RECLASS CharId ClassId
[3540] RECLASS_FROMCHAR CharId OtherCharId
[3541] SWITCH_CLASSES CharId OtherCharId
```

Changes matchin [units](#unit-parameters) class.

- `RECLASS` sets matching units class to `ClassId`.
- `RECLASS_FROMCHAR` sets matching units class to the default class of the (other) given character.
- `SWITCH_CLASSES` sets matching units class to the default class of the (other) given character, and sets unit matching other characters class to the class the first matching unit was in before.

**Note**: Only the first character paramater follow the [standard unit lookup rules](#unit-parameters). The second one just gets a unit by comparing raw character id.

---

</details>

<details>
<summary>36 : check in area (CHECK_INAREA)</summary>

```
[3640] CHECK_INAREA CharId [XTopLeft, YTopLeft] [Width, Height]
```

Gets `1` if the [matching units](#unit-parameters) position is within the box defined by given parameters, `0` otherwise.

---

</details>

<details>
<summary>37 : give item or gold (GIVE_ITEM, GIVE_MONEY, TAKE_MONEY)</summary>

```
[3720] GIVE_ITEM CharId
[3721] GIVE_MONEY CharId
[3722] TAKE_MONEY
```

- `GIVE_ITEM` gives new item based on item id in `s3` to [matching unit](#unit-parameters), and displays popup accordingly.
- `GIVE_MONEY` gives money amount in `s3` to [matching units](#unit-parameters) faction, and displays popup accordingly.
- `TAKE_MONEY` silently takes away money amount in `s3` from blue (player) faction. This will not allow money underflow.

**Note**: standard EA raws have those named `GIVEITEMTO` (alright), `GIVEITEMTOMAIN` (what), and `GIVETOSLOT3` (tf) respectively.

---

</details>

<details>
<summary>38 : set active unit (SET_ACTIVE)</summary>

```
[3820] SET_ACTIVE CharId
```

Sets [matching unit](#unit-parameters) as active unit (while doing the necessary bookkeeping for changing active unit if necessary).

**Note**: This hangs if this can't find any matching unit.

---

</details>

<details>
<summary>39 : change AI scripts (CHAI)</summary>

```
[3920] CHAI CharId
[3921] CHAI [X, Y]
```

Changes the matching units (or unit at given position) primary (AI1) and secondary (AI2) AI scripts based on the content of `s1`.

`s1` needs to formatted as follows: `0x0000YYXX`, with `YY` corresponding to AI2, and `XX` to AI1.

If AI2 is changed to `0x13`, no change occurs. If AI1 is changed to `0x15`, no change occurs.

**Note**: This **doesn't** follow the [standard unit lookup rules](#unit-parameters)! Instead, `[3920]` will apply the AI changes to *all* units with matching character ids!

**Note**: This only will change the AI *scripts*. There is no way to change AI *parameters* (aka AI3 and AI4) through events without using ASMCs.

---

</details>

<details>
<summary>3A : popups (NOTIFY, BROWNTEXTBOX)</summary>

```
[3A40] NOTIFY TextId SongId <Unused?>
[3A41] BROWNTEXTBOX TextId [0, 0xYYXX]
```

TODO

**Note**: standard EA raw for `BROWNTEXTBOX` is misconfigured hence why the position argument is weird.

---

</details>

<details>
<summary>3B : display cursor (CURSOR, CURSOR_REMOVE, CURSOR_FLASHING)</summary>

TODO

---

</details>

<details>
<summary>3C : TODO (TODO)</summary>

---

</details>

<details>
<summary>3D : configure disabled menu commands (-)</summary>

```
[3D20] - <Bits>
[3D21] - <Bits>
```

Disables menu commands based on given bits.

- `[3D20]` completely removes the commands from the menu.
- `[3D21]` grays commands out, but have them still displayed.

Bit list for `[3D20]` (byte table at `FE8U:080D793F`):

| Bit | Command Id | Corresponding command(s) |
| --- | ---------- | ------------------------ |
| `0`  | `4F` | (Unit Menu) Attack |
| `1`  | `51` | (Unit Menu) Staff |
| `2`  | `6B` | (Unit Menu) Wait |
| `3`  | `63` | (Unit Menu) Rescue |
| `4`  | `64` | (Unit Menu) Drop |
| `5`  | `5C` | (Unit Menu) Visit |
| `6`  | `5A` | (Unit Menu) Talk |
| `7`  | `67` | (Unit Menu) Item |
| `8`  | `37` | (Item Menu) Discard |
| `9`  | `68` | (Unit Menu) Trade |
| `10` | `69` | (Unit Menu) Supply |
| `11` | `5B` | (Unit Menu) Support |
| `12` | `5F` | (Unit Menu) Armory |
| `13` | `71` | (Map Menu) Options |
| `14` | `78` | (Map Menu) End (turn) |

Bit list for `[3D21]` (byte table at `FE8U:080D794E`):

| Bit | Command Id | Corresponding command(s) |
| --- | ---------- | ------------------------ |
| `0` | `49` | (Attack Weapon Select Menu) Item 1 |
| `1` | `4A` | (Attack Weapon Select Menu) Item 2 |
| `2` | `4B` | (Attack Weapon Select Menu) Item 3 |
| `3` | `4C` | (Attack Weapon Select Menu) Item 4 |
| `4` | `4D` | (Attack Weapon Select Menu) Item 5 |

Used for turorials, probably.

---

</details>

<details>
<summary>3E : Open Prep Screen (PREP)</summary>

```
[3E20] PREP
```

Starts prepscreen.

Clears eid `0x84`, effectively enabling various map sprite related icons.

**Note**: The event engine is still running, and will continue its execution normally after the prep screen ends.

---

</details>

<details>
<summary>3F : Scripted battles (TODO)</summary>

TODO

---

</details>

<details>
<summary>40 : Promote unit (PROM)</summary>

TODO

---

</details>

<details>
<summary>41 : Warp animations (WARP_IN, WARP_OUT)</summary>

TODO

---

</details>

<details>
<summary>42 : TODO (TODO)</summary>

TODO

---

</details>

<details>
<summary>43 : TODO (TODO)</summary>

TODO

---

</details>

<details>
<summary>44 : TODO (TODO)</summary>

TODO

---

</details>

<details>
<summary>45 : TODO (TODO)</summary>

TODO

---

</details>
