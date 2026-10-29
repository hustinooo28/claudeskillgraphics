#!/bin/sh
# Render the saved scene in short chunks, each in a fresh Blender process (a long single run slows down
# progressively with the depth compositor on the software GL driver). Resumable: finished frames are kept.
# usage: BLENDER=/path/to/blender sh render_chunks.sh FIRST LAST [CHUNK]
FIRST=$1; LAST=$2; CHUNK=${3:-80}
a=$FIRST
while [ $a -le $LAST ]; do
  b=$((a + CHUNK - 1)); [ $b -gt $LAST ] && b=$LAST
  "$BLENDER" -b build/scene.blend --python-expr "import bpy; s=bpy.context.scene; s.frame_start=$a; s.frame_end=$b; bpy.ops.render.render(animation=True)" > build/chunk.log 2>&1
  echo "chunk $a-$b done $(date +%T)"
  a=$((b + 1))
done
