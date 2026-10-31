#!/bin/sh
# ranger's preview script: images through image-preview, everything else through pistol
# (~/.config/pistol/pistol.conf). Exit codes are ranger's (0 show stdout, 1 no preview,
# 7 ranger draws the file as an image).
# Arguments from ranger: FILE WIDTH HEIGHT IMAGE_CACHE_PATH PREVIEW_IMAGES(True|False)
file=$1 width=$2 height=$3 images=$5

case $(file --dereference --brief --mime-type -- "$file") in
  image/*) RANGER_IMAGES=$images exec image-preview "$file" "$width" "$height" ;;
esac
pistol "$file" || exit 1
