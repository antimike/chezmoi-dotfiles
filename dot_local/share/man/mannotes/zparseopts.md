# zparseopts(1n)

## Summary
A utility for parsing CLI options in zsh/zutil.

## Description

### Usage
```zsh
set -- -a A -b B -c --file F
zparseopts -D -E -A opts -- a: b: c -file:
```

### Options
        -a      Default array in which to store options
        -A      Associative array in which to store options
        -D      Remove parsed opts from positional params
        -E      Don't stop option parsing at first nonrecognized param
        -F      Fail on first option-like, nonrecognized param
