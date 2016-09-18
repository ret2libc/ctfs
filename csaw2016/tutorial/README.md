# Tutorial

The vulnerability in this binary is in plain sight.
The function number 1, `Manual`, is useful to have a reference inside the libc,
given together with the service, while the function number 2, `Practice`,
contains a buffer overflow on the stack.

Let's get some info about the service:
```sh
$ file ./tutorial
./tutorial: ELF 64-bit LSB  executable, x86-64, version 1 (SYSV), dynamically linked (uses shared libs), for GNU/Linux 2.6.24, BuildID[sha1]=01e9b94153bb138f2dda5b5b9c490da7c255c68d, not stripped

$ checksec ./tutorial
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE
```

So it seems like we have to do ret-to-libc/ROP and to bypass the canary. ASLR,
even if not enabled on the server (it can be checked easily by connecting multiple
times to the server and using the first menu option), wouldn't be a problem
because of the `Manual` function that can leak an address inside the libc.

By decompiling the function related to the `Practice` functionality we get:
```C
__int64 __fastcall func2(int a1)
{
  char s[312]; // [sp+10h] [bp-140h]@1
  __int64 v3; // [sp+148h] [bp-8h]@1

  v3 = *MK_FP(__FS__, 40LL);
  bzero(s, 300);
  write(a1, "Time to test your exploit...\n", 0x1DuLL);
  write(a1, ">", 1);
  read(a1, s, 460);
  write(a1, s, 324);
  return *MK_FP(__FS__, 40LL) ^ v3;
}
```

Not only we have a stack-based buffer overflow, but there is also a `write`
function that always prints 324 bytes, including the canary value.

The exploit should:
* get the address inside the libc with the `Manual` function
* use `Practice` to leak the canary
* use `Practice` again to pass the canary check and overwrite the return address
* enjoy

We can't directly return to the system function because we have to load in
`rdi` the address of the string `/bin/sh`. Moreover, the server communicates
with the client through a socket, not with stdin/stdout, so we must redirect
the socket to stdin/stdout to receive and send commands. The file descriptor
number of the client socket can be guessed and it was 4 as expected.
