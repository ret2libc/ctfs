# Shelling Folder

First, I got some info about the binary:
```
$ file shellingfolder_42848afa70a13434679fac53a471239255753260
shellingfolder_42848afa70a13434679fac53a471239255753260: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.32, BuildID[sha1]=011a2a4e3b9edc0ee9b08578c62ca76dec45ef64, stripped

$ checksec ./shellingfolder_42848afa70a13434679fac53a471239255753260
[!] Couldn't find relocations against PLT to get symbols
[*] '/security/ctfs/hitconquals2016/shellingfolder/shellingfolder_42848afa70a13434679fac53a471239255753260'
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      PIE enabled
```

There is no canary, so maybe it's something stack related, but there is PIE and
Full RELRO. The program lets you create/list/remove folders and files, with an
interface like this:
```
**************************************
            ShellingFolder
**************************************
 1.List the current folder
 2.Change the current folder
 3.Make a folder
 4.Create a file in current folder
 5.Remove a folder or a file
 6.Caculate the size of folder
 7.Exit
**************************************
Your choice:
```

After playing with the binary I was able to make it crash just by adding a
file with a long name and then calculating the size. I used the De Bruijn
sequence and valgrind to find out that the characters from the 24th to the 31th
were used as an address inside the "calculate size" function.

Looking at that function we see:
```C
memset(s, 0, 32uLL);
while ( i <= 9 )
{
  if ( folder->subfilesdirs[i] )
  {
    ptr_sz = &folder->size;
    copy_string(s, folder->subfilesdirs[i]->name);
    if ( folder->subfilesdirs[i]->is_folder == 1 )
    {
      *ptr_sz = *ptr_sz;
    }
    else
    {
      printf("%s : size %ld\n", s, folder->subfilesdirs[i]->size);
      *ptr_sz += folder->subfilesdirs[i]->size;
    }
  }
  ++i;
}
printf("The size of the folder is %ld\n", folder->size);
```

The buffer `s` is just 24 bytes, but the name can be 31 chars, so here is where
the buffer overflow happens. It appears that we are able to overwrite just the
`ptr` variable, that is then dereferenced with:
```C
*ptr_sz += folder->subfilesdirs[i]->size;
```

This looks like a write primitive that allow us to modify the value of any
address we want: just put the address inside the name of a new file and set its
size in such a way that the old value plus the file size is equal to the
desired final value.

There are two problems though. First, we don't know any address, not even the
ones of the binary itself (because of PIE). Second, we need the value at a
specific address before changing it. Thus we absolutely need a leak. Looking
carefully at `copy_string` function:
```C
void *copy_string(void *a1, const char *a2)
{
  size_t n;

  n = strlen(a2);
  return memcpy(a1, a2, n);
}
```
It uses a memcpy, so it doesn't put the `\0` at the end of the buffer and if I
have a name with just 24 bytes, the following `printf` in the "calculate size"
function will print `s` with some "garbage" after it, that is the content of
`ptr_sz` that lies just after `s`.

So I have a pointer inside the heap (because `ptr_sz` would point to
`&folder->size`). I couldn't leak whatever I want, yet.

On the heap there is the folder structure that contains, among other things,
pointers to subfolders and files inside a dir. It looks like this:
```C
struct folder_t {
	struct folder_t **subfilesdirs;
	struct folder_t *parent_folder;
	char name[32];
	long size;
	int is_folder;
	char field_84;
}
```

How can I use it to leak some info? The "list" function prints all
subfolders/files inside a dir and in particular it prints the names. By
creating a fake sub-folder that points to the address I want to leak (-88
because of the offset of the `name` field inside the structure), I can get the
data I want. The idea is this:
* create two files with the right name/size (see exp.py for more details)
* calculate the size of the current folder. At this point, the files that I
  just created should trigger the vuln and write the fake sub-folder pointer in
  the root folder (detail: I needed two files to make it work because the sizes
  are just 32bits but the pointer I want to write is 64).
* list all subfolders/files to leak the data pointed by the fake sub-folder
* delete the two previous files to keep the state of the program clean

At this point I had a leak, but I wasn't able to find anything useful on the
heap that pointed to other libraries or to the binary itself. I played a little
bit with the heap by creating and deleting dirs, so that free would place some
libc pointers in the free chunks. Then, I leaked the values and knew where the
libc was.

Inside the libc I found a pointer to the stack(it was the `environ` pointer)
and from there a pointer inside the binary. At that point I had everything
needed to hijack the control flow of the program.

The write primitive is pretty much like the read one:
* create two files with the right name/size
* calculate the size of the current folder, so that the two files trigger the
  vuln that writes the value at the address I want
* delete the two previous files to keep the state of the program clean

To be honest, I immediately tried to overwrite the GOT, but obviously it failed
(by the time I got here I forgot about Full RELRO :) ). After this, I tried to
overwrite the return address of the "calculate size" function itself. Since I
needed more than one use of the vuln to prepare the ROP chain, I couldn't
directly overwrite the return address, but I placed the chain some bytes above
the main stack frame. When all was set, I overwrote the return address with a
stack-pivoting gadget, to execute `system('/bin/sh')` and get a shell.

The exploit wasn't 100% reliable, but it worked :)




If you find any mistake or have a better solution, feel free to open an issue
or contact me!
