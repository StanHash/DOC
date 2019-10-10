
Note: `sz` refers to the size of an area. `<addr>-sz` is used when `<addr>` refers to the end of an area rather than the start of it (when `sz` is unknown/variable).

# ALWAYS FREE RAM SPACE

| Start addr | Size     | Condition | Notes
| ---------- | -------- | --------- | -----
| `03003750` | `0x268`  | -         | In area where ARM funcs get copied. Unreferenced functions.
| `03003B48` | `0xBC`   | -         | Untested. In area where ARM funcs get copied. Unreferenced function.
| `03003F48` | `0x208`  | -         | Untested. In area where ARM funcs get copied. Past end of meaningful data.
| `0300428C` | `0x6D4`  | -         | Untested. In area where Interrupt handler gets copied. Past end of meaningful data.
| `030067A8` | -        | ?         | Untested. End of static IWRAM. May collide with stack.
| `02026AD0` | `0x360`  | Using IconRework/CIconDisplay | Used by vanilla icon display system.
| `02026E30` | `0x2028` | Not Using debug printing | Unused unless digging up leftover debug stuff.
| `02040000-sz` | ~`0xC00` | -    | End of EWRAM. May collide with unit loading buffer (sizes of `0xC00` and less should leave enough room for 50+ units).

Note that `02026AD0+360` = `02026E30`, which is the start of another free block. Which means that `02026AD0` can be considered as being a single `0x2388` bytes long free block.

## Smaller free areas

There exist a few more instances of free blocks that are used by unused/unreferenced functions (I only added in the big one which is the debug printing stuff).

For example, there is `0x20` free bytes at `030005B0`, which is normally used to build up a proc script in RAM by unreferenced function at `0800D4D4`.

## Free bytes from alignment padding

There exists numerous instances of small 1 or 2 byte blocks of free space that was caused by alignment requirements of certain objects.

For example, at `03000006` are 2 free bytes, being after a 3 short array (6 bytes), but before a word that needed to be 4-aligned.

# SOMETIMES FREE RAM SPACE

| Start addr    | Size     | When not free            | Notes
| ------------- | -------- | ------------------------ | -----
| `02020188-sz` | ?        | During battle animations | -
| `0203AAA4`    | `0x1B80` | During link arena        | May be only in *real* link games, in which case it may as well be considered always free.
| `0203EFB8`    | `0x1048` | During unit loading      | Up to the end of EWRAM

TODO: more of this

# KNOWN USED SPACE FROM HACKS

[Used this thread as reference](https://feuniverse.us/t/information-on-the-ram-area-that-the-patch-uses-independently/3334?u=stanh), as well as my own knowledge of existing hacks.

| Hack name                   | Start addr     | Size     | Notes
| --------------------------- | -------------- | -------- | -----
| Mode 7 style stuff (CHAX)   | `03003750`     | `0x208`+ | `0x140` + size of ram func (currently `0xC8`)
| Improved Sound Mixer        | `03006CB0`     | `0x860`  | ram func (may free `0x400` bytes at `03002C60`?)
| Improved Sound Mixer        | `03007510`     | `0x380`  | new mixing buffer
| AutoNewline                 | `02026E30`     | variable | string buffer
| FE8 Battle Transform        | `0203AABE`     | `2`      | unknown when used.
| Battle Buffer ext (SkillSystem) | `0203AAC0` | `0xF8`+  | frees `0x1C` bytes at `0203A5EC`
| ArenaLimits                 | `0203AAC0`     | variable | string buffer
| HpBars (SkillSystem)        | `0203AE00`     | `0xC8`   | Warning cache. Uses 2, then indexes byte array by unit id (`0xC6` is past the last unit id).
| 7743's unit select sfx      | `0203B1F0`     | `0x10`   | unknown when used.
| break_save                  | `0203B200`     | `0x400`  | probably repointed convoy? (which would free `0xC8` bytes at `0203A81C`)
| Debuffs 'fix' (SkillSystem) | `0203ED40`(!!) | variable | This conflicts with a bunch of things! (Including chapter completion stats).
| Gaiden-style Magic          | `0203F080`     | `4`      | Probably not used during unit loading so that's safe.
| Debuffs (SkillSystem)       | `0203F100`(!)  | `0x900`  | array of 8 byte entries indexed by unit id leaves a bunch of holes.
| Debuffs (VBA/make)          | `0203FBB8`     | `0x448`  | -
