
Note: `sz` refers to the size of an area. `<addr> - sz` is used when `<addr>` refers to the end of an area rather than the start of it (when `sz` is not unknown/variable).

# ALWAYS FREE RAM SPACE

| Start addr | Size     | Condition | Notes
| ---------- | -------- | --------- | -----
| `03003750` | `0x268`  | -         | In area where ARM funcs gets copied. Vanilla only calls the ROM versions of those.
| `03003B48` | `0xBC`   | -         | In area where ARM funcs gets copied. Unreferenced function.
| `030067A8` | -        | ?         | End of static IWRAM. May collide with stack.
| `02026AD0` | `0x360`  | Using IconRework/CIconDisplay | Used by vanilla icon display system.
| `02026E30` | `0x2028` | Not Using debug printing | Unused unless digging up leftover debug stuff.
| `02040000 - sz` | ~`0xC00` | -    | End of EWRAM. May collide with unit loading buffer (hence approx size).

Note that `02026AD0+360` = `02026E30`, which is the start of another free block. Which means that `02026AD0` can be considered as being a single `0x2388` bytes long free block.

# SOMETIMES FREE RAM SPACE

| Start addr | Size     | When not free            | Notes
| ---------- | -------- | ------------------------ | -----
| `0203AAA4` | `0x1B80` | During link arena        | May be only in *real* link games, in which case it may as well be considered always free
| `02020188 - sz` | ?   | During battle animations | -
| `0203EFB8` | `0x1048` | During unit loading      | Up to the end of EWRAM

# KNOWN USED SPACE FROM HACKS

[Used this thread as reference](https://feuniverse.us/t/information-on-the-ram-area-that-the-patch-uses-independently/3334?u=stanh), as well as my own knowledge of existing hacks.

| Hack name                   | Start addr     | Size     | Notes
| --------------------------- | -------------- | -------- | -----
| M7 (CHAX)                   | `03003750`     | `0x208`+ | `0x140` + size of ram func (currently `0xC8`)
| Improved Sound Mixer        | `03006CB0`     | ?        | ram func (may free `0x400` bytes at `03002C60`?)
| Improved Sound Mixer        | `03007510`     | ?        | sound mixing buffer?
| FE8 Battle Transform        | `0203AABE`     | `2`      | unknown when used.
| Battle Buffer ext (SkillSystem) | `0203AAC0` | `0xF8`+  | frees `0x1C` bytes at `0203A5EC`
| 7743's unit select sfx      | `0203B1F0`     | `0x10`   | unknown when used.
| break_save                  | `0203B200`     | `0x400`  | probably repointed convoy? (which would free `0xC8` bytes at `0203A81C`)
| Debuffs 'fix' (SkillSystem) | `0203ED40`(!!) | ?        | Non-free! This is in where the chapter completion stats are stored!
| Gaiden-style Magic          | `0203F080`     | `4`      | Probably not used during unit loading so that's safe.
| Debuffs (SkillSystem)       | `0203F100`(!)  | `0x900`  | 8 byte array indexed by unit id leaves a bunch of holes.
| Debuffs (VBA/make)          | `0203FBB8`     | `0x448`  | -
