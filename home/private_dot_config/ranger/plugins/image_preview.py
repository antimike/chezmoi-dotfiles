"""Turn ranger's image preview on with the kitty method when ranger runs in kitty.

ranger 1.9.4 has no sixel method, so elsewhere (Windows Terminal on WSL2, foot, a console)
image preview stays off and scope.sh's image-preview prints chafa block characters instead.
"""

import os

import ranger.api

_hook_init = ranger.api.hook_init


def hook_init(fm):
    if os.environ.get("KITTY_WINDOW_ID") or os.environ.get("TERM") == "xterm-kitty":
        fm.settings.preview_images_method = "kitty"
        fm.settings.preview_images = True
    return _hook_init(fm)


ranger.api.hook_init = hook_init
