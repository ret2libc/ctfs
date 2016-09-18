# Aul

There was no binary given with this challenge.
I tried to connect to the service and after playing for some seconds I found
out that with the `help` command a lot of "garbage" was sent out by the server.
I used a simple python script to extract the binary data and put it in a file.

Looking quickly at it, it looks like the code of the server itself, but `file`
is not able to say anything, although `hexdump` was more helpful.
```
00000000  4c 75 61 53 00 19 93 0d  0d 0a 1a 0d 0a 04 08 04  |LuaS............|
00000010  08 08 78 56 00 00 00 00  00 00 00 00 00 00 00 28  |..xV...........(|
00000020  77 40 01 00 00 00 00 00  00 00 00 00 00 02 02 1f  |w@..............|
00000030  00 00 00 2c 00 00 00 08  00 00 80 2c 40 00 00 08  |...,.......,@...|
00000040  00 80 80 2c 80 00 00 08  00 00 81 2c c0 00 00 08  |...,.......,....|
00000050  00 80 81 2c 00 01 00 08  00 00 82 2c 40 01 00 08  |...,.......,@...|
00000060  00 80 82 2c 80 01 00 08  00 00 83 2c c0 01 00 08  |...,.......,....|
00000070  00 80 83 2c 00 02 00 08  00 00 84 08 80 c2 84 2c  |...,...........,|
00000080  40 02 00 08 00 80 85 2c  80 02 00 08 00 00 86 2c  |@......,.......,|
00000090  c0 02 00 08 00 80 86 06  80 43 00 41 c0 03 00 24  |.........C.A...$|
000000a0  40 00 01 06 40 43 00 24  40 80 00 26 00 80 00 10  |@...@C.$@..&....|
000000b0  00 00 00 04 0b 6d 61 6b  65 5f 62 6f 61 72 64 04  |.....make_board.|
000000c0  0f 70 6f 70 75 6c 61 74  65 5f 62 6f 61 72 64 04  |.populate_board.|
000000d0  0f 62 6f 61 72 64 5f 74  6f 73 74 72 69 6e 67 04  |.board_tostring.|
```

I tried to compile a lua program myself to check if the first bytes were
similar and they were, except for an initial byte `\x1b` and a different letter
after the `Lua` signature (that changes with every version of Lua).

I added the first byte and looked on the Internet for a Lua decompiler, finding
`unluac` (https://sourceforge.net/projects/unluac/). It didn't work out of the
box though, complaining that the signature wasn't a valid Lua one.

Indeed, after carefully comparing the dump of a program I compiled myself and
the one downloaded from the server, I found out that each `\x0a` was prefixed
by a `\x0d`. Done also this step, I was able to decompile Lua with `unluac` and
get the source code.

In particular, this is the output of the `run_step` function:
```lua
function run_step(A0_41)
  local L1_42, L2_43
  L1_42 = readline
  L1_42 = L1_42()
  L2_43 = string
  L2_43 = L2_43.len
  L2_43 = L2_43(L1_42)
  if L2_43 == 0 then
    L2_43 = exit
    L2_43()
    L2_43 = nil
    return L2_43
  end
  L2_43 = string
  L2_43 = L2_43.find
  L2_43 = L2_43(L1_42, "function")
  if L2_43 then
    L2_43 = nil
    return L2_43
  end
  L2_43 = string
  L2_43 = L2_43.find
  L2_43 = L2_43(L1_42, "print")
  if L2_43 then
    L2_43 = nil
    return L2_43
  end
  L2_43 = load
  L2_43 = L2_43("return " .. L1_42)
  L2_43 = L2_43()
  if L2_43 == nil then
    return nil
  end
  return L2_43(A0_41)
end
```

The input command is used to find a function with that name, with `return
function_name`, that is immediately called. I thought that I could use it to
execute a "system" function and get a shell and it worked :) (except the
function is called `os.execute` and not `system`).
