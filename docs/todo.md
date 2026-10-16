## Files to add

- zsh stuff
  - [ ] powerlevel10k
  - [ ] marker
  - [ ] completion scripts
  - [ ] widgets and other snippets
  - [ ] funky / gfunky
- shared files / appdata
  - man pages
  - tldr
  - marker
  - readmes
- scripts
  - cache manpages
  - wifi and other FZF widgets
  - sshstart, etc.
- wallpaper
- kitty
- i3
- ipython
- nvim

## TODO

- [ ] systemd
  - [ ] geoclue + init location finder
  - [ ] document and install deps
- [ ] wallpaper
  - [ ] clone wallpaper repo
    - [ ] init script?
  - [ ] get pywal

- [ ] general
  - [X] clone /etc repo (init script?)
    - not an intended use-case of Chezmoi
  - [ ] follow website instructions to write pass clone script
  - [X] figure out sleep / lid close settings
    - `xset s off`
    - /etc/systemd/logind.conf

## Dependency specification

Things A User Cares About:
- services and abstractions provided ("capabilities")
- admissible constraints
  - another way of categorizing this: possible **configuration options**
- any incompatibilities with other services / apps
- ease of use / discoverability
- *contexts* in which the services or abstractions are relevant / useful
  - can the service be configured effectively **from the context in which it is useful**?
  - are the service's capabilities **discoverable from within that context**?
- (some) direct dependencies

Things A User Doesn't Care About:
- filesystem minutiae
- transitive dependencies
- version management
  - "just get the latest one that works"
- build errors
- RPC / IPC mechanisms / implementations

---

Configuration management is a hard problem because users do not think in terms of abstract data structures--they think in terms that are directly relevant to the tasks they are actually trying to accomplish, which may or may not be known by the designers of the software and/or configuration system.  Many of the metrics we use to gauge our experience with software--"how do I **get it to** format this text the way I want," "why won't it **let me** do this," etc.--are dialectical in nature, and thus intrinsically "fuzzy."  Such concepts do not lend themselves to representation by cleanly-defined abstractions.

Even more problematic is the fact that users have a tendency to focus exclusively on the capabilities they need, to the extent that software that requires them to manage--or even be aware of--its dependencies, the conceptual models and assumptions inherent to its design, or any other details of its implementation, no matter how relevant to the programmer, is often deemed simply unusable (or not worth the effort of using).  After all, the *whole point* of using software is to delegate uninteresting computations to the computer.  Maintaining a constant "mental configuration buffer" on behalf of the software takes precious energy away from the presumably more important mental activities on which the user would prefer to focus.

The upshot of this is that a good configuration system must allow users to specify constraints on **arbitrary nodes** of an extended "graph of dependencies" of the software, and to group or declare those constraints in any order they see fit.  This graph of dependencies may or may not include any of the actual, *concrete* dependencies that are of primary interest to the programmer.  It is virtually certain, however, that it will contain many nodes which are not only *not* "dependencies" in the programmer's sense, but whose relationships to the concrete dependencies are more or less ill-defined.
