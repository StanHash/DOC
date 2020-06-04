# World Map Event Master Doc

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

### Non-worldmap event codes that work in worldmap mode

This list is incomplete, these are just the ones I've personally tested:

- ENUT, ENUF, CHECK_EVENTID and conditionals
- EVBIT_MODIFY, EVBIT_T, EVBIT_F
- CALL
- STAL
- FADI, FADU
- MUSC
- TEXTCONT
- TEXTEND

## The Code Doc

This lists all event codes from 80 to CD (hex) by id. 00 to 45 are covered in EventCodes.md.

<details>
<summary>80 : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>81 : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>82 : end world map (ENDWM)</summary>

```
[8220] ENDWM
```

- `ENDWM` ends world map event execution, equivalent to `ENDA` (?)

---

</details>

<details>
<summary>83 : set camera? (WM_SETCAM)</summary>

```
[8340] WM_SETCAM CamX CamY
```

Untested; appears to center the camera on the given coordinates (in pixels?)

---

</details>

<details>
<summary>84 : unknown (TODO)</summary>

```
[8440] WM_SETCAMONLOC 0x0 LocationID 0x0
```

Under investigation. I have this alternately documented as both WM_SETCAMONLOC and something involving skirmishes???

---

</details>

<details>
<summary>85 : set camera on sprite (WM_SETCAMONSPRITE, WM_CENTERCAMONLORD)</summary>

```
[8540] WM_SETCAMONSPRITE 0x0 SpriteID 0x0
[8540] WM_CENTERCAMONLORD
```

Centers the camera on a mapsprite.

`SpriteID` is the index of the given sprite in the GmapMU array, which is assigned via PUTSPRITE. 0x0 is the lord unit by default.

A version without parameters is aliased as WM_CENTERCAMONLORD; all parameters are treated as 0 in this case, centering the camera on the lord unit (id 0).

---

</details>

<details>
<summary>86 : arbitrary camera move (WM_MOVECAM)</summary>

```
[8680] WM_MOVECAM 0x0 EndX EndY 0x1 Speed Delay 0x0
```

Moves the camera to an arbitrary coordinate. (What units?) (I've had trouble getting this to work.)

`-1` in `EndX` and `EndY` will center the camera on the next story destination.

---

</details>

<details>
<summary>87 : move camera to location (WM_MOVECAMTO)</summary>

```
[8780] WM_MOVECAMTO StartX StartY LocationID Speed Delay
```

Centers the camera on `LocationID`. 

`-1` in `StartX` and `StartY` will cause it to start at the current camera position.

Standard speed and delay are `0x20` and `0x1` respectively.

---

</details>

<details>
<summary>88 : unknown (TODO)</summary>

```
[TODO] Event88_ unknown
```

Probably is camera-related, given its location?

---

</details>

<details>
<summary>89 : wait for camera (WM_WAITFORCAM) </summary>

```
[8920] WM_WAITFORCAM 
```

Pauses event execution until the camera has finished moving.

---

</details>

<details>
<summary>8A : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>8B : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>8C : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>8D : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>8E : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>8F : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>90 : draw worldmap path with FX (WM_DRAWPATH)</summary>

```
[9040] WM_DRAWPATH 0x0 PathID 0x0
```

Draws the given path ID with a fade-in transition and a sound effect. Also rewrites the pathfinding map with the new path information, to determine which locations can be walked to.

---

</details>

<details>
<summary>91 : draw worldmap path silently (WM_DRAWPATH2)</summary>

```
[9140] WM_DRAWPATH2 0x0 PathID 0x0
```

Draws the given path ID silently. Also rewrites the pathfinding map with the new path information, to determine which locations can be walked to.

---

</details>

<details>
<summary>92 : remove worldmap path (WM_REMOVEPATH)</summary>

```
[9240] WM_REMOVEPATH 0x0 PathID 0x0
```

Removes the given path ID from the map. Also rewrites the pathfinding map with the new path information, to determine which locations can be walked to.

---

</details>

<details>
<summary>93 : draw worldmap location silently (WM_LOADLOCATION2)</summary>

```
[9340] WM_LOADLOCATION2 0x0 LocationID 0x0
```

Draws the given location ID silently.

---

</details>

<details>
<summary>94 : remove worldmap location (WM_REMOVELOCATION)</summary>

```
[9440] WM_REMOVELOCATION 0x0 LocationID 0x0
```

Removes the given worldmap location.

---

</details>

<details>
<summary>95 : draw worldmap non-story location with FX (WM_LOADLOCATION3)</summary>

```
[9540] WM_LOADLOCATION3 0x0 LocationID 0x0
```

Draws the given location ID with a blue glowy effect and a sound effect, but does not set them as a story location. Used for tower/ruins/Melkaen Coast.

---

</details>

<details>
<summary>96 : draw worldmap replacement path (WM_DRAWPATH3)</summary>

```
[9640] WM_DRAWPATH3 0x0 PathID 0x0
```

Used in vanilla chapter 17 for the road between Mulan and Renais when the two lords reunite.

---

</details>

<details>
<summary>97 : draw worldmap location with FX and set as destination (WM_CREATENEXTDESTINATION)</summary>

```
[9720] WM_CREATENEXTDESTINATION
```

Draws the given location ID with a blue glowy effect and a sound effect, and sets bit &2 in its WMDataStruct entry to mark it as the next story destination.

---

</details>

<details>
<summary>98 : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>99 : wait for special effects to end (WM_WAITFORFX)</summary>

```
[9920] WM_WAITFORFX
```

Stalls event execution until special effects have finished.

---

</details>

<details>
<summary>9A : mark location as next story location (WM_SETDESTINATION)</summary>

```
[9A40] WM_SETDESTINATION 0x0 LocationID 0x0
```

Sets bit &2 in `LocationID`'s WMDataStruct entry to mark it as a story location and place the red flag above its sprite. Walking onto that location will trigger the chapter beginning events for the associated chapterID of the location.

---

</details>

<details>
<summary>9B : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>9C : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>9D : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>9E : allocate a GmapMU entry (PUTSPRITE)</summary>

```
[9E60] PUTSPRITE MuID ClassID Allegiance LocationID
```

In WMDataStruct there is an array of 7 slots for MoveUnit data, this allows mapsprites to be drawn on the worldmap.

MuID is the index in this array to configure. ClassID is which class's map sprite to use. Allegiance is 0 for blue unit, 1 for red unit and 2 for green unit. LocationID is which node to start the sprite at.

---

</details>

<details>
<summary>9F : TODO</summary>

```
[TODO] 
```

Under investigation.

---

</details>

<details>
<summary>A0 : deallocate a GmapMU entry (REMSPRITE)</summary>

```
[A040] REMSPRITE MuID
```

In WMDataStruct there is an array of 7 slots for MoveUnit data, this allows mapsprites to be drawn on the worldmap.

MuID is the index in this array to free up. This command will hide the sprite so that its ID can be reused later.

---

</details>
