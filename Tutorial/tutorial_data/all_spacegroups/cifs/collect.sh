#!/bin/bash

SOURCE="$1"
DIRS=$(cd "$SOURCE"; ls | sort -n)

for group in $DIRS; do
    (
	cd "$SOURCE/$group"
	SMALLEST=$(ls | sort -n -r | tail -n 1)
	LAST=$(ls "$SMALLEST"/ | tail -n 1)
	LAST2=$(ls "$SMALLEST"/"$LAST" | tail -n 1)
	echo "$SOURCE/$group/$SMALLEST/$LAST/$LAST2 $group.cif"
    )
done | while read COPYLINE; do
    cp $COPYLINE 
done

#for file in *.cif; do
#    GROUP=$(cat "$file" | awk '/_symmetry_Int_Tables_number/{print $2}')
#    mv "$file" "$GROUP.cif"
#done
