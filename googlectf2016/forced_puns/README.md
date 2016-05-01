# Forced Puns

Let's do a `file` as a first thing:
```bash
$ file ./app/forced-puns
./app/forced-puns: ELF 64-bit LSB  shared object, ARM aarch64, version 1 (SYSV), dynamically linked (uses shared libs), for GNU/Linux 3.7.0, BuildID[sha1]=a677e5ead33f8ac9d3948e8157cdcfa39b3f9701, not stripped
```

Aarch64, never seen its assembly before, but there's always a first time.
Let's load it with r2.

```
$ r2 -AA ./app/forced-puns

[0x00000e20]> e asm.emu=true
[0x00000e20]> e asm.emustr=true
[0x00000e20]> e asm.describe=true # this was really helpful for me to have an idea of what instructions do

[0x00000e20]> s main
```

I spent a lot of time trying to run the binary. At the end I used
`qemu-aarch64-static` on a Debian vagrant box, attaching gdb to do some
debugging during the exploitation.

Playing with the binary a little bit, I noticed that there was a buffer overflow
when creating a new entry with a name longer than 232 bytes.

```
$ qemu-aarch64-static -g 12345 -E LD_PRELOAD=./lib/aarch64-linux-gnu/libc.so.6 -L ./lib ./app/forced-puns
$ gdb-multiarch ./app/forced-puns
> target remote localhost:12345
> c
```

The segfault is happening in the function `end_of_entry`. Thanks to this
function I was able to understand a little bit the structure allocated on the
heap, that was something like this:

```
// size of the structure is 256
struct entry {
	char *large;
	long small;
	struct entry *next;
	char name[232];
}
```

It seems like `end_of_entry` segfaults because my input ends up in the `next` field
of the next entry I was going to allocate. That function is called everytime
you set the name of a new entry to know the place the input will be copied to.
So if I can put in the `next` field the address of the printf got (or any
other function) I can execute the code I want.

But first we should get some leaks, because ASLR is enabled and the binary is
PIE. Setting the `large` field of an entry and printing it allows you to get the
address of a chunk of memory in the heap. Moreover when you print an entry, the
small value is printed as "%s" and this allows you to leak other addresses. I
used the overflow in the name to overwrite the `small` field of the next entry,
so that I could get the leak when printing the entries.

But how to know where the binary was loaded? Looking at the heap I saw a pointer
to `end_of_entry`, that I used to get a leak of the binary address and, after
that, I used the got entries in the binary to leak addresses of the libc.

At this point I had every address I wanted, I just needed to find a function
pointer to overwrite. At first I tried to overflow something in .got.plt, but I
realized I couldn't do that because some requirements were needed in order for
the overwrite to work as expected. This is more or less what `end_of_entry` does
and how it's used:
```
struct entry *end_of_entry(struct entry *root) {
	while (root->next) {
		root = root->next;
	}
	return root;
}

struct entry *p = end_of_entry(root_ptr);
strcpy(p->name, input);
```

The idea was to to overwrite the `next` field of an entry in such a way that
`end_of_entry` would return the value where I wanted to overwrite (minus 0x18,
the offset of the field name in the structure `entry`). In order for this to
work, there has to be a 0 in the qword just before the address I want to
overwrite, so that it will be interpreted as the `next` field of the entry and
the fake entry would be considered the last one. So I couldn't really write
everywhere...

I tried to overwrite the `end_of_entry` pointer at the start of the heap, but
because of some differences in the memory layout between my local environment
and the one on the server I wasn't able to solve the challenge in this way.

After a while I found a pointer to a pointer to the `end_of_entry` function (in
the .got) and luckily it was preceeded by a 0. I then use my write primitive to
put in the bss the address of the system (and the address of the bss where i put
the address of the system). Now, whenever the program calls `end_of_entry` it
would instead call system. Last thing I needed to do was to make root points to
the `/bin/sh` string, but it was quite easy at this point to overwrite the first
bytes of the first entry in the heap to insert the string.

You can find the full exploit in exp.py.
