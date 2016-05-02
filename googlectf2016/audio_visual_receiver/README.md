# Audio visual receiver

I worked on this challenge with @hanyone and @castor91, but at the end @rpaleari
solved it with the old but gold (smart) brute force.

The program is very simple: it has 6 functions named `up`, `down`, `left`,
`right`, `a`, `b` that change in some ways a global `state` variable and a
`check` one. Moreover, the `a` function is the one that outputs the final flag.

The binary asks for one character at a time, calling `up` if the char is 'u',
`down` if the char is 'd' and so on. On each inserted char the value of the
`state` variable is inserted in a global buffer. That's the same buffer that is
XORed with the encrypted flag. So we just need to find the right sequence of
functions that changes the state in the right way.

Let's see what those functions look like:
```python
def up(state, check, pos, cross_pos):
	check ^= state
	buffer[pos] = state
	pos = (pos + 1) % 33
	state *= 3 # each function changes the state in a different way
	return (state, check, pos, cross_pos)

...

def a(state, check, pos, cross_pos):
	check ^= state
	buffer[pos] = state
	pos = (pos + 1) % 33
	state = (state * 16) | (state >> 4)
	if cross[cross_pos] == check:
		check = 0
		cross_pos += 1
		if pos > 29:
			return print_flag()
```

First thing I thought was to use Z3. How to write the right constraints? We can
think about it as an array of `check` variables and an array of `state`
variables that represent the check/state variable at the i-th char.

`check` changes (almost) always in the same way:
```
xor_check = check[i] == check[i - 1] ^ state[i - 1]
```
Instead `state` can be changed in 6 different ways, depending on the character
you write (u, d, l, r, a, b):
```
state[i] == (state[i-1] * 3) # up
state[i] == (state[i-1] >> 1) * 8) - (state[i-1] >> 1) # down
state[i] == (state[i-1] * 2) # left
state[i] == (state[i-1] >> 3)) | (state[i-1]*32) # right
state[i] == (state[i-1] * 16) | (state[i-1] >> 4) # a
state[i] == ~(state[i-1]) # b
```
`cross_ptr` always remains the same as the previous value, except in some cases
when you press 'a', in particular when the check `cross[cross_pos] == check` is
satisfied.

Notice that `state[i] ^ flag[i]` should give us our real flag, so we can add
some constraints to make this value printable and also specify that the first
four chars have to be "CTF{" and the last one "}". We can also specify that the
last function to be executed has to be 'a', by specifying what should be the
value of `state[len(flag)]`.

At this point I ran my script expecting to find the flag soon, but I had many
problems... I spent a lot of time trying to debug it, giving up after a while.
Luckily another member of our team was able to solve the chal by bruteforcing.

After the competition I've chosen to look again at my approach and I've
rewritten and rechecked all constraints again, but still nothing. Only after a
while I have realized what a big mistake I made... Looking at the disassembly of the
functions you can see that many of them are using the SHR instruction, which is
a *logical shift to the right*. Python and z3 use, instead, the *arithmetical
right shift*.

Indeed, fixing my constraints (and my python script) to use the logical shift,
I was able to get the flag quickly.
