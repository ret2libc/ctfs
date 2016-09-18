# hungman

I tried to play a little bit with the service and it looked like a hangman game
with random data. Luckily, while I was playing, I noticed that if the name
inserted at the start of the game was long enough, all the letters were in the
hidden string and in this way I was always able to win just by trying all the
letters.

After decompiling the binary I looked mainly at two functions: the one executed
at the start of the game, to create the player structure, and the one that
handles the game and in particular the "change name" functionality, executed
after winning the game.

```C
struct player *__cdecl get_player()
{
  char *v0; // ST10_8@3
  player *pl; // ST18_8@3
  struct player *result; // rax@3
  __int64 v3; // rbx@3
  int len_name; // [sp+Ch] [bp-124h]@1
  char *v5; // [sp+10h] [bp-120h]@1
  char name[248]; // [sp+20h] [bp-110h]@1
  __int64 v7; // [sp+118h] [bp-18h]@1

  v7 = *MK_FP(__FS__, 40LL);
  write(1, "What's your name?\n", 0x12uLL);
  memset(name, 0, 248uLL);
  len_name = read(0, name, 247uLL);
  v5 = strchr(name, '\n');
  if ( v5 )
    *v5 = 0;
  v0 = (char *)malloc(len_name);
  pl = (player *)malloc(0x80uLL);
  memset(pl, 0, 0x80uLL);
  pl->name = v0;
  pl->len_name = len_name;
  memcpy(pl->name, name, len_name);
  result = pl;
  v3 = *MK_FP(__FS__, 40LL) ^ v7;
  return result;
}
```
```C
...
  puts("High score! change name?");
  __isoc99_scanf(" %c", &v2.choice);
  if ( v2.choice == 'y' )
  {
    newname = malloc(248uLL);
    memset(newname, 0, 248uLL);
    len_newname = read(0, newname, 248uLL);
    pl->len_name = len_newname;
    v11 = strchr((const char *)newname, '\n');
    if ( v11 )
      *v11 = 0;
    memcpy(pl->name, newname, len_newname);
    free(newname);
  }
  snprintf(high_player_str, 0x200uLL, "Highest player: %s", pl->name);
  highscore = pl->score;
...
```

Indeed, the vulnerability was there, when changing the name player. The new
name is copied in the buffer of the old name, though without reallocating the
space. So if the new name is longer than the old one, you can overwrite
something on the heap.

With gdb I tried to see what is on the heap after the name, looking for
something interesting to overwrite.
```
0x15a5010:      0x4141414141414141      0x4141414141414141 <- name
0x15a5020:      0x4141414141414141      0x0000414141414141
0x15a5030:      0x0000000000000000      0x0000000000000091
0x15a5040:      0x00000041000000d9      0x00000000015a5010 <- player struct
0x15a5050:      0x0000000000000000      0x0101000101010100
0x15a5060:      0x0100010101010101      0x0000000000000001
0x15a5070:      0x0000000000000000      0x0000000000000000
0x15a5080:      0x0000000000000000      0x0000000000000000
```

Inside the player structure there is a pointer to the name that looks quite good.
By overwriting it, the next "change name" would try to write at the overwritten
address, providing me a write primitive. At this point I just have to change
the right .got.plt entry to execute the `system` function with `/bin/sh` as
first argument. After a while it looked like `strchr` was a good candidate.

At last, I needed an info leak to bypass ASLR, but that was quite easy to find
because when changing the player name pointer, the pointed string was printed
on stdout, giving me the address of the `strchr` function.

In summary:
* use an initial player name longer than 25
* win the game by using all the letters
* change the player name to overwrite the player name pointer inside the
  structure with the address of the `strchr` got.plt entry
* get the address of `strchr` to bypass ASLR
* win again the game
* change the player name again. This time the new name is written to the
  `strchr` got.plt entry. Of course, I want to replace this entry with the
  address of `system`.
* now I just have to make the program execute `strchr`, to trigger `system`.
  To do this I can just win again the game and change the name with `/bin/sh`.
  This string is passed to `strchr`/`system`, giving me the shell.
