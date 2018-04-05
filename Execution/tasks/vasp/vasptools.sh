#!/bin/bash

# Assumes VASP5 POSCAR format (how else could we generate POTCARs?)

#Expects VASP_PSEUDOLIB to be set consistently to e.g. /path/to/.../POT_GGA_PAW_PBE/

function VASP_MAGMOMLINE {
    local POSCAROCCUPATIONLINE=7

    local POSCARMAGMOM=$(cat POSCAR | awk 'NR==1 && /MAGMOM=/ {print $0}' | sed 's/^.*\[MAGMOM=\([^]]*\).*$/\1/')

    if [ -n "$POSCARMAGMOM" ]; then
	echo "$POSCARMAGMOM"
	return
    fi

    local MAGMOM=$(awk -v "line=$POSCAROCCUPATIONLINE" 'NR==line { for(i=1;i<=NF;i++) { printf("%d*5 ",$i) } }' POSCAR)

    if [ -z "$MAGMOM" ]; then
	echo "Error in VASP_MAGMOMLINE: could not calculate MAGMOM." >&2
	exit 1
    fi

    echo "$MAGMOM"
}

function VASP_NBANDSLINE {
    # Reimplementation of the algorithm of cif2cell. NBANDS is the max of the default in VASP spin-polarized (0.6*nelect + NIONS/2), non-spin: (nelect/2 + NIONS/2), occupied bands + 20, or 0.6*nelect + total initalized magnetic moment
    # In addition, it must be divisible by NPAR, so we round up to that.

    if [ ! -e "POSCAR" -o ! -e "POTCAR" -o ! -e "INCAR" ]; then
	echo "VASP_NBANDSLINE: VASP INPUT FILES MISSING." >&2
	exit 1
    fi

    local ZVALS=$(awk -F'=' '/^ *POMASS.*; *ZVAL *=/{gsub(" +","");gsub("[^=0-9.]+",""); print $3}' POTCAR)

    if [ -z "$ZVALS" ]; then
	echo "VASP_NBANDSLINE: Could not extract Z-vals from POTCAR" >&2
	exit 1
    fi

    local POSCAROCCUPATIONLINE=7
    local COUNTS=$(awk -v "line=$POSCAROCCUPATIONLINE" 'NR==line { for(i=1;i<=NF;i++) { print $i } }' POSCAR)

    if [ -z "$COUNTS" ]; then
	echo "VASP_NBANDSLINE: Could not extract atom counts from POSCAR." >&2
	exit 1
    fi

    local NATOMS=$(awk -v "line=$POSCAROCCUPATIONLINE" 'NR==line { for(i=1;i<=NF;i++) { sum+=$i } print sum}' POSCAR)

    if [ -z "$NATOMS" ]; then
	echo "VASP_NBANDSLINE: Could not extract number of atoms from POSCAR." >&2
	exit 1
    fi

    local NMAG=$(awk -F'=' '/^MAGMOM/ { split($2,a," +"); for (x in a) { if (a[x] == "") { continue }; split(a[x],b,"\\*"); if (b[2] == "") { sum += b[1] } else { sum += b[1]*b[2] } }; print sum; exit}' INCAR)

    if [ -z "$NMAG" ]; then
	echo "VASP_NBANDSLINE: Could not extract MAGMOM line from INCAR." >&2
	exit 1
    fi

    local ISPIN=$(awk -F'=' '/^ISPIN/ { gsub("[^=0-9.]+",""); print $2; exit}' INCAR)

    if [ -z "$ISPIN" ]; then
	echo "VASP_NBANDSLINE: Could not extract ISPIN information from INCAR." >&2
	exit 1
    fi

    local NELECT=$(echo "" | awk -v "COUNTS=$COUNTS" -v "ZVALS=$ZVALS" ' END { split(ZVALS,azval," "); split(COUNTS,acount," "); for(i=1; i <= length(acount); i++) { sum+=azval[i]*acount[i]} print sum}')

    local NBANDS=1
    local NBANDS2=1
    local NBANDS3=1

    if [ $NATOMS -lt 6 ]; then
	NATOMS=6
    fi

    # TODO: Add support for noncollinear
    if [ "$ISPIN" -eq 2 ]; then
	NBANDS=$(echo "" | awk -v "NELECT=$NELECT" -v "NATOMS=$NATOMS" 'function ceiling(x){return x%1 ? int(x)+1 : x} END {print int(0.6*NELECT + 1)+ceiling(NATOMS/2)}')
        NBANDS2=$(echo "" | awk -v "NELECT=$NELECT" -v "NMAG=$NMAG" 'function ceiling(x){return x%1 ? int(x)+1 : x} END {print int(0.6*NELECT + 1)+ceiling(NMAG/2)}')
	NBANDS3=$(echo "" | awk -v "NELECT=$NELECT" 'function ceiling(x){return x%1 ? int(x)+1 : x} END {print int(0.6*NELECT + 1)+20}')

	#echo "GOT: NELECT=$NELECT NATOMS=$NATOMS NMAG=$NMAG $NBANDS $NBANDS2 $NBANDS3" >&2
    else
	NBANDS=$(echo "" | awk -v "NELECT=$NELECT" -v "NATOMS=$NATOMS" 'function ceiling(x){return x%1 ? int(x)+1 : x} END {print int(NELECT/2 + 2)+ceiling(NATOMS/2)}')
	NBANDS2=$NBANDS
	NBANDS3=$(echo "" | awk -v "NELECT=$NELECT" 'function ceiling(x){return x%1 ? int(x)+1 : x} END {print ceiling(NELECT/2)+20}')
    fi

    if [ -z "$NBANDS" -o -z "$NBANDS2" -o -z "$NBANDS3" ]; then
	echo "Error in VASP_NBANDSLINE: could not calculate NBANDS." >&2
	exit 1
    fi

    if [ "$NBANDS2" -gt "$NBANDS" ]; then
	NBANDS=$NBANDS2
    fi

    if [ "$NBANDS3" -gt "$NBANDS" ]; then
	NBANDS=$NBANDS3
    fi

    # Vasp can generally get unhappy with an uneven number of bands...
    if [ $(( NBANDS % 2)) -ne 0 ]; then
	NBANDS=$((NBANDS+1))
	ADDED=1
    else
	ADDED=0
    fi

    local NPAR=$(VASP_GET_TAG NPAR)
    if [ -n "$NPAR" ]; then
	MISMATCH=$(( NBANDS % NPAR))
	if [ $MISMATCH -ne 0 ]; then
	    NBANDS=$((NBANDS+$MISMATCH))
	fi
    fi

    if grep "^BUMP_BANDS$" ht.remedy.* >/dev/null 2>&1; then
	if [ "$ADDED" == 1 ]; then
	    NBANDS=$((NBANDS-1))
	else
	    NBANDS=$((NBANDS+1))
	fi
    fi

    if [ -n "$NPAR" ]; then
	MISMATCH=$(( NBANDS % NPAR))
	if [ $MISMATCH -ne 0 ]; then
	    NBANDS=$((NBANDS+$MISMATCH))
	fi
    fi

    echo "$NBANDS"
}

function VASP_KPOINTSLINE {
    local LVAL=$1

    if [ -z "$LVAL" ]; then
	echo "Error in VASP_KPOINTSLINE: must be called with a KPOINT density. (l parameter in VASP manual on automatic KPOINT generation.)" >&2
	return
    fi

    if grep "^EQUAL_KPTS$" ht.remedy.* >/dev/null 2>&1; then
	EQUAL_KPTS=1
    else
	EQUAL_KPTS=0
    fi

    if grep "^BUMP_KPTS$" ht.remedy.* >/dev/null 2>&1; then
	BUMP_KPTS=1
    else
	BUMP_KPTS=0
    fi

    #
    # We do things a bit differently than the corresponding routine in VASP.
    # We always round up (ceiling)
    # We always generate a symmetrix grid N x N x N to wase a lot of computational time
    # but avoid scary warnings about reciprocal grid not matching the real grid
    #
    #       b1len=abs((v2[2] * v3[3] + v2[3] * v3[1] + v2[1] * v3[2] - v2[2] * v3[1] - v2[1] * v3[3] - v2[3] * v3[2])/(celldet*scale))
    #       b2len=abs((v1[1] * v3[3] + v1[2] * v3[1] + v1[3] * v3[2] - v1[3] * v3[1] - v1[2] * v3[3] - v1[1] * v3[2])/(celldet*scale))
    #       b3len=abs((v1[1] * v2[2] + v1[2] * v2[3] + v1[3] * v2[1] - v1[3] * v2[2] - v1[2] * v2[1] - v1[1] * v2[3])/(celldet*scale))

    local KPTSLINE=$(awk -v "LVAL=$LVAL" -v"equalkpts=$EQUAL_KPTS" -v"bumpkpts=$BUMP_KPTS" '
         function ceiling(x){return x%1 ? int(x)+1 : x}
         function abs(x){return ((x < 0.0) ? -x : x)}
         NR==2 {scale=$1;}; NR==3 {split($0,v1," ");} NR==4 {split($0,v2," ");} NR==5 {split($0,v3," ");}
         END {
           celldet = v1[1] * v2[2] * v3[3] + v1[2] * v2[3] * v3[1] + v1[3] * v2[1] * v3[2] - v1[3] * v2[2] * v3[1] - v1[2] * v2[1] * v3[3] - v1[1] * v2[3] * v3[2] 

           cellvol = abs(celldet)

           if (cellvol < 1e-6) {
              print "Error in VASP_KPOINTSLINE: singular cell vectors. POSCAR is broken." > "/dev/stderr"
              exit
           }

           if(scale < 0.0) {
             scale = (-scale/cellvol)**(1.0/3.0)
           }

           b1len=sqrt(abs(v2[2]*v3[1]-v2[1]*v3[2])**2 + abs(v2[3]*v3[1]-v2[1]*v3[3])**2+abs(v2[3]*v3[2]-v2[2]*v3[3])**2)/(celldet*scale)
           b2len=sqrt(abs(v1[2]*v3[1]-v1[1]*v3[2])**2 + abs(v1[3]*v3[1]-v1[1]*v3[3])**2+abs(v1[3]*v3[2]-v1[2]*v3[3])**2)/(celldet*scale)
           b3len=sqrt(abs(v1[2]*v2[1]-v1[1]*v2[2])**2 + abs(v1[3]*v2[1]-v1[1]*v2[3])**2+abs(v1[3]*v2[2]-v1[2]*v3[3])**2)/(celldet*scale)

           N1=ceiling(LVAL*b1len+0.5)
           if (N1 < 3) { N1 = 3}

           N2=ceiling(LVAL*b2len+0.5)
           if (N2 < 3) { N2 = 3}

           N3=ceiling(LVAL*b3len+0.5)
           if (N3 < 3) { N3 = 3}

           if (bumpkpts==1) {
             N1+=1; N2+=1; N3+=1;
           }

           if (equalkpts==1) {
              NMAX=N1
              if (N2 > NMAX) {NMAX=N2}
              if (N3 > NMAX) {NMAX=N3}
              print NMAX,NMAX,NMAX
           } else {
              print N1,N2,N3
           }
         }' POSCAR)

    if [ -z "$KPTSLINE" ]; then
	echo "Error in VASP_KPOINTSLINE: could not calculate KPOINTS." >&2
	exit 1
    fi

    echo "$KPTSLINE"
}

function VASP_PREPARE_POTCAR {

    local POSCAR=$1
    local POTCAR=$2

    if [ -z "$POSCAR" ]; then
	POSCAR="POSCAR"
    fi

    if [ -z "$POTCAR" ]; then
	POTCAR="POTCAR"
    fi

    if [ -z "$VASP_PSEUDOLIB" ]; then
	echo "Error in VASP_PREPARE_POTCAR: must set \$VASP_PSEUDOLIB to path for VASP pseudopotential library." >&2
	exit 1
    fi

    rm -f "$POTCAR"

    local POSCARSPECIESLINE=6
    local SPECIESLIST=$(awk -v "line=$POSCARSPECIESLINE" 'NR==line { for(i=1;i<=NF;i++) { printf("%s ",$i) } }' "$POSCAR")
    for SPECIES in $SPECIESLIST; do
	for PRIORITY in "_3" "_2" "_d" "_pv" "_sv" "" "_h" "_s"; do
	    if [ -d "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}" ]; then
	      if [ -e "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR" ]; then
		  cat "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR" >> "$POTCAR"
		  continue 2
	      fi
	      if [ -e "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.Z" ]; then
		  zcat "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.Z" >> "$POTCAR"
		  continue 2
	      fi
	      if [ -e "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.gz" ]; then
		  zcat "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.gz" >> "$POTCAR"
		  continue 2
	      fi
	      if [ -e "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.bz2" ]; then
		  bzcat "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.bz2" >> "$POTCAR"
		  continue 2
	      fi
	    fi
	done
	echo "Error in VASP_PREPARE_POTCAR: could not find pseudopotential for: $SPECIES" >&2
	echo "VASP_PSEUDOLIB was set to: $VASP_PSEUDOLIB" >&2
	exit 1
    done
}

function VASP_POSCAR_SCALE_VOLUME {
    XSCALE=$1

    mv POSCAR ht.tmp.POSCAR
    awk -v "XSCALE=$XSCALE" '
         NR<2 || NR>2 {print $0}
         NR==2 {l0=$0; scale=$1; print scale*XSCALE;}
         ' ht.tmp.POSCAR > POSCAR
    rm -f ht.tmp.POSCAR
}

function VASP_CHECK_AND_FIX_POSCAR {
    mv POSCAR ht.tmp.POSCAR
    awk '
         function ceiling(x){return x%1 ? int(x)+1 : x}
         NR<2 || NR>5 {print $0}
         NR==2 {l0=$0; scale=$1;}; NR==3 {l1=$0;split($0,v1," ");} NR==4 {l2=$0;split($0,v2," ");}
         NR==5 {
           l3=$0
           split($0,v3," ");

           celldet = v1[1] * v2[2] * v3[3] + v1[2] * v2[3] * v3[1] + v1[3] * v2[1] * v3[2] - v1[3] * v2[2] * v3[1] - v1[2] * v2[1] * v3[3] - v1[1] * v2[3] * v3[2]

           if (celldet < 0.0) {

              if (v1[1] != 0.0) { v1[1] = -v1[1] }
              if (v1[2] != 0.0) { v1[2] = -v1[2] }
              if (v1[3] != 0.0) { v1[3] = -v1[3] }

              if (v2[1] != 0.0) { v2[1] = -v2[1] }
              if (v2[2] != 0.0) { v2[2] = -v2[2] }
              if (v2[3] != 0.0) { v2[3] = -v2[3] }

              if (v3[1] != 0.0) { v3[1] = -v3[1] }
              if (v3[2] != 0.0) { v3[2] = -v3[2] }
              if (v3[3] != 0.0) { v3[3] = -v3[3] }

              print scale
              printf("%20.16f %20.16f %20.16f\n", v1[1], v1[2], v1[3])
              printf("%20.16f %20.16f %20.16f\n", v2[1], v2[2], v2[3])
              printf("%20.16f %20.16f %20.16f\n", v3[1], v3[2], v3[3])
           } else {
              print l0
              print l1
              print l2
              print l3
           }
         }
         ' ht.tmp.POSCAR > POSCAR
    rm -f ht.tmp.POSCAR
}

function VASP_EXTRACT_POTIM {
    if [ ! -e "OUTCAR" ]; then
	echo "VASP_EXTRACT_POTIM: Missing OUTCAR file" >&2
	exit 1
    fi

    local POTIM=$(awk -F' *= *' '
      /^ *opt step *=/{split($2,a," +"); optstep=a[1]} END {print optstep}
    ' OUTCAR)
    if [ -z "$POTIM" ]; then
	echo "Error in VASP_EXTRACT_POTIM: Could not extract POTIM from OUTCAR" >&2
	exit 1
    fi

    echo "$POTIM"
}

function VASP_EXTRACT_NBR_PLANEWAVES {
    if [ ! -e "OUTCAR" ]; then
	echo "VASP_EXTRACT_POTIM: Missing OUTCAR file" >&2
	exit 1
    fi

    local NBRPW=$(awk -F' *: *' '
      /^ *maximum number of plane-waves:/{print $2; exit}
    ' OUTCAR)
    if [ -z "$NBRPW" ]; then
	echo "Error in VASP_EXTRACT_NBR_PLANEWAVE: Could not extract." >&2
	exit 1
    fi

    echo "$NBRPW"
}


function VASP_PREPARE_KPOINTS {

    local LVAL=$1
    local TYPE=$2

    if [ -z "$LVAL" ]; then
	LVAL=20
    fi

    local LINE=$(VASP_KPOINTSLINE "$LVAL")

    if [ -z "$LINE" ]; then
	echo "Error in VASP_PREPARE_KPOINTS: VASP_PREPARE_KPOINTS got empty KPOINTSLINE" >&2
	exit 1
    fi

    if [ -z "$TYPE" ]; then
	if grep "^GAMMA_KPTS$" ht.remedy.* >/dev/null 2>&1; then
	    TYPE="Gamma"
	else
	    TYPE="Monkhorst-pack"
	fi
    fi

    cat > KPOINTS <<EOF
Automatic mesh generated by run.sh
0
$TYPE
$LINE
0. 0. 0.
EOF

}

function VASP_PREPARE_INCAR {
    ACCURACY=$1
    EDIFFMARGIN=$2

    if [ ! -e POSCAR ]; then
	echo "VASP_PREPARE_INCAR: Missing POSCAR file" >&2
	exit 1
    fi

    if [ ! -e "INCAR" ]; then
	echo "VASP_PREPARE_INCAR: Need a base INCAR file to start from." >&2
	exit 1
    fi

    local POSCAROCCUPATIONLINE=7
    local NATOMS=$(awk -v "line=$POSCAROCCUPATIONLINE" 'NR==line { for(i=1;i<=NF;i++) { sum+=$i } print sum}' POSCAR)

    if [ -z "$ACCURACY" ]; then
        if grep "^EDIFF_SMALLER$" ht.remedy.* >/dev/null 2>&1; then
            ACCURACY=0.0001
        elif grep "^EDIFF_SMALLER_2$" ht.remedy.* >/dev/null 2>&1; then
            ACCURACY=0.00001
        else
            ACCURACY=0.001
        fi
        DEFAULT_ACCURACY=1
    else
        DEFAULT_ACCURACY=0
    fi
    if [ -z "$EDIFFMARGIN" ]; then
	local NSW=$(VASP_GET_TAG "NSW")
	if [ -n "$NSW" ]; then
	    if [ "$NSW" -gt "1" ]; then
		# Relaxations are typically improved by increasing the electronic convergence,
		# since then more accurate ionic steps are taken
		EDIFFMARGIN=500
	    else
		EDIFFMARGIN=33
	    fi
	else
	    EDIFFMARGIN=33
	fi
    fi

    if [ "$ACCURACY" != '-1' ]; then
	local EDIFF=$(VASP_GET_TAG "EDIFF")
	local EDIFFG=$(VASP_GET_TAG "EDIFFG")
	if [ -z "$EDIFF" -o "$DEFAULT_ACCURACY" == 0 ]; then
	    EDIFF=$(HT_FCALC "max(($ACCURACY) * ($NATOMS) / ($EDIFFMARGIN),1e-6)")
	    VASP_SET_TAG EDIFF $EDIFF
	fi
	if [ -z "$EDIFFG" -o "$DEFAULT_ACCURACY" == 0 ]; then
	    EDIFFG=$(HT_FCALC "max(($ACCURACY) * ($NATOMS),1e-4)")
	    VASP_SET_TAG EDIFFG $EDIFFG
	fi
    fi

    local NPAR=$(VASP_GET_TAG NPAR)
    if [ -z "$NPAR" -a -n "$HT_NBR_NODES" ]; then
	NPAR=$(HT_FCALC "int(sqrt($HT_NBR_NODES))")
	if [ "$NPAR" -le 1 ]; then
	    NPAR=1
	fi
	VASP_SET_TAG "NPAR" "$NPAR"
    fi

    if grep "^NPARONE$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG "NPAR" "1"
    fi

    local MAGMOMS=$(VASP_GET_TAG MAGMOMS)
    if [ -z "$MAGMOMS" ]; then
	LINE=$(VASP_MAGMOMLINE)
	if [ -z "$LINE" ]; then
	    echo "Error in VASP_PREPARE_INCAR: got empty MAGMOM line" >&2
	    exit 1
	fi
	VASP_SET_TAG "MAGMOM" "$LINE"
    fi

    local NBANDS=$(VASP_GET_TAG NBANDS)
    if [ -z "$NBANDS" ]; then
	LINE=$(VASP_NBANDSLINE)
	if [ -z "$LINE" ]; then
	    echo "Error in VASP_PREPARE_INCAR: got empty NBANDS line" >&2
	    exit 1
	fi
	VASP_SET_TAG "NBANDS" "$LINE"
    fi

    if grep "^NOSYM$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG ISYM 0
    fi

    if grep "^GAUSSMEAR$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG ISMEAR 0
	VASP_SET_TAG SIGMA 0.05
    fi

    if grep "^LREALFALSE$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG LREAL ".FALSE."
    fi

    if grep "^SOFTMIX$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG ICHARG 2
	VASP_SET_TAG AMIX 0.10
	VASP_SET_TAG BMIX 0.01
    fi

    if grep "^SOFTMIX2$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG ICHARG 2
	VASP_SET_TAG BMIX 3.00
	VASP_SET_TAG AMIN 0.01
    fi

    if grep "^ALGOALL$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG ALGO ALL
	VASP_SET_TAG TIME 0.4
    fi

    if grep "^ALGOALL2$" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG ALGO All
	VASP_SET_TAG TIME 0.05
    fi

    if grep "^ALGODAMPED" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG ALGO Damped
	VASP_SET_TAG TIME 0.05
    fi

    if grep "^LOWSYMPREC" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG SYMPREC 1e-4
    fi

    if grep "^HIGHSYMPREC" ht.remedy.* >/dev/null 2>&1; then
	VASP_SET_TAG SYMPREC 1e-6
    fi

    local ICHARG=$(VASP_GET_TAG ICHARG)
    if [ -n "$ICHARG" ]; then
	if [ "$ICHARG" -eq 1 ]; then
	    if [ ! -e "CHGCAR" -o -s "CHGCAR" ]; then
		VASP_SET_TAG ICHARG 2
	    elif grep "^CHGCAR_INCOMPLETE" ht.controlled.msgs; then
		VASP_SET_TAG ICHARG 2
	    fi
	fi
    fi
    
    local NEDOS=$(VASP_GET_TAG NEDOS)
    if [ -z "$NEDOS" ]; then
	if grep "^BUMP_NEDOS$" ht.remedy.* >/dev/null 2>&1; then
	    VASP_SET_TAG NEDOS 1000
	fi
    fi
}

function VASP_CHECK_PATH_LENGTH {
  if [ ${#PWD} -gt 240 ]; then
    echo "Path is longer than 240 characters!"
    echo "This could cause unpredictable errors."
    HT_TASK_ATOMIC_SECTION_END_BROKEN
  fi
}

function VASP_PREPARE_CALC {
    VASP_CHECK_AND_FIX_POSCAR
    VASP_PREPARE_KPOINTS
    VASP_PREPARE_INCAR
    VASP_CHECK_PATH_LENGTH
}

function VASP_PRECLEAN {
    rm -f WAVECAR CONTCAR PCDAT IBZKPT EIGENVAL XDATCAR OSZICAR OUTCAR DOSCAR CHG CHGCAR vasprun.xml PROCAR
}

function VASP_STDOUT_CHECKER {
    local MSGFILE="$1"
    local EXITPID="$2"

    ISYM=$(VASP_GET_TAG ISYM)
    if [ -z "$ISYM" ]; then
	ISYM=1
    fi

    echo "STDOUT_CHECKER ACTIVE $EXITPID"
    echo "STDOUT_CHECKER ACTIVE $EXITPID" > "$MSGFILE"

    # TODO: Check and fix awk version issue and fflush, system
    awk -v"msgfile=$MSGFILE" -v"ISYM=$ISYM" '
    /WARNING: Sub-Space-Matrix is not hermitian in DAV/ && subherm_count>5 { next }
    /hit a member that was already found in another star/ && star_count>5 { next }
    /^ *-?[0-9]+\.[0-9]+(E-?[0-9]+)? *$/ && simple_number>=100 { next }

    /WARNING: chargedensity file is incomplete/ {print "CHGCAR_INCOMPLETE" >> msgfile; exit 2}

    {print $0; system("");}

    /^ *-?[0-9]+\.[0-9]+(E-?[0-9]+)? *$/ { simple_number+=1; if (simple_number == 99) {print "SPEWS_SINGLE_LINE_VALUES" >> msgfile} }
    /WARNING: Sub-Space-Matrix is not hermitian in DAV/ { subherm_count += 1 }
    /hit a member that was already found in another star/ { star_count += 1}

    /LAPACK: Routine ZPOTRF failed/ {print "ZPOTRF" >> msgfile; exit 2}
    /Reciprocal lattice and k-lattice belong to different class of lattices./ { print "KPTSCLASS" >> msgfile; if(ISYM!=0) { exit 2 } }
    /ZBRENT: can'"'"'t locate minimum, use default step/ && zbrent!=1 {print "ZBRENT" >> msgfile; zbrent=1}

    /ZBRENT: fatal error in bracketing/ {print "ZBRENT_BRACKETING" >> msgfile;}

    /One of the lattice vectors is very long/ {print "TOOLONGLATTVEC" >> msgfile; exit 2}

    /Tetrahedron method fails for NKPT<4/ {print "TETKPTS" >> msgfile; exit 2}
    /Fatal error detecting k-mesh/ {print "TETKPTS" >> msgfile; exit 2}
    /Fatal error: unable to match k-point/ {print "TETKPTS" >> msgfile; exit 2}
    /Routine TETIRR needs special values/ {print "TETKPTS" >> msgfile; exit 2}

    /inverse of rotation matrix was not found/ {print "INVROTMATRIX" >> msgfile; exit 2}

    # BRMIX errors can be recovered from, so let the program run its course.
    /BRMIX: very serious problems/ {print "BRMIX" >> msgfile;}

    /Routine TETIRR needs special values/ {print "TETIRR" >> msgfile;}

    /Could not get correct shifts/ {print "SHIFTS" >> msgfile;}

    /REAL_OPTLAY: internal error/ {print "REAL_OPTLAY" >> msgfile;}

    /internal ERROR RSPHER/ {print "RSPHER" >> msgfile;}

    /WARNING: DENTET: can'"'"'t reach specified precision/ {print "DENTET" >> msgfile;}

    /unoccupied bands, you have included TOO FEW BANDS/ {print "NBANDS" >> msgfile;}

    /ERROR: the triple product of the basis vectors/ {print "TRIPLEPRODUCT" >> msgfile;}

    /Found some non-integer element in rotation matrix/ {print "ROTMATRIX" >> msgfile;}

    /BRIONS problems: POTIM should be increased/ {print "BRIONS" >> msgfile;}

    /WARNING: small aliasing \(wrap around\) errors must be expected/ {print "ALIASING" >> msgfile}

    /The distance between some ions is very small/ {print "TOOCLOSE" >> msgfile; exit 2}

    /Therefore set LREAL=.FALSE. in the  INCAR file/ {print "LREALFALSE" >> msgfile; exit 2}

    /Sorry, number of cells and number of vectors did not agree./ {print "PRICELL" >> msgfile; exit 2}

    /ERROR FEXCF: supplied exchange-correlation table/ {FEXCF=1; print "FEXCF" >> msgfile;}
    /is too small, maximal index :/ && FEXCF==1 {exit 2;}

    /internal error in RAD_INT: RHOPS \/= RHOAE/ {print "RADINT" >> msgfile; exit 2;}

    /internal ERROR in NONLR_ALLOC/ {print "NONLR_ALLOC" >> msgfile; exit 2;}

    /Error EDDDAV: Call to ZHEGV failed./ {print "EDDAV_ZHEGV" >> msgfile;}

    /WARNING: CNORMN: search vector ill defined/ {print "CNORMN" >> msgfile;}

    '
    RETURNCODE="$?"

    echo "STDOUT_CHECKER END (CODE=$RETURNCODE)" >> "$MSGFILE"

    return "$RETURNCODE"
}


function VASP_OSZICAR_CHECKER {
    local MSGFILE="$1"
    local EXITPID="$2"

    # First grab needed parameters from the OUTCAR
    OUTCARPARAMS=$(HT_TASK_FOLLOW_FILE OUTCAR "$EXITPID" | awk '
      /^ *NELM / {gsub(/[,;]/,""); nelm=$3; gotnelm=1}
      /^ *NSW / {gsub(/[,;]/,""); nsw=$3; gotnsw=1}
      gotnsw==1 && gotnelm==1 {print nelm, nsw; exit 0}
    ')

    echo "OSZICAR_CHECKER ACTIVE WITH PARAMS: $OUTCARPARAMS" > "$MSGFILE"
    # Now we can follow the OSZICAR
    HT_TASK_FOLLOW_FILE OSZICAR "$EXITPID" 3600 | awk -v"OUTCARPARAMS=$OUTCARPARAMS" -v"msgfile=$MSGFILE" '
    BEGIN {
      split(OUTCARPARAMS,a," ");
      nelm=a[1]; nsw=a[2];
    }

    /^[A-Za-z]+: +([0-9]+) +([-+0-9.Ee]+) +([-+0-9.Ee]+) +([-+0-9.Ee]+) +([0-9]+) +([-+0-9.Ee]+) +([-+0-9.Ee]+)/ {
       nstep=$2
       lastrmsc=$7
    }
    /^[A-Za-z]+: +([0-9]+) +([-+0-9.Ee]+) +([-+0-9.Ee]+) +([-+0-9.Ee]+) +([0-9]+) +([-+0-9.Ee]+)/ {
       nstep=$2
    }
    /^ +[0-9]+ F= ([-+0-9.Ee]+) / {
       istep+=1
       energy=$5
       # print "NSTEP:",nstep, nelm
       # print "NSW:",istep, nsw
       if(energy > 0) {lastep=1}
       if(lastrmsc >= 0.7) {print "BADCONV ELEC (RMSC>=0.7)" >> msgfile; lastebad=1}
       if(nstep >= nelm) {print "BADCONV ELEC (N>=NELM)" >> msgfile; lastebad=1}
       if(nsw>1 && istep >= nsw) {print "BADCONV ION (ISTEP>=NSW)" >> msgfile; lastibad=1}

       if(energy < 0) {lastep=0}
       if(lastebad && lastrmsc < 0.7 && nstep < nelm) {print "RECOVERED CONV ELEC" >> msgfile; lastebad=0;}
       if(lastibad && nsw>1 && istep < nsw) {print "RECOVERED CONV ION" >> msgfile; lastibad=0;}

       if(quit) { exit 2 }
    }
    /^ *HT_TIMEOUT/ { print "OSZICAR_TIMEOUT" >> msgfile; exit 2 }

    END {
       if(lastebad) {print "LAST BADCONV ELEC" >> msgfile;}
       if(lastibad) {print "LAST BADCONV ION" >> msgfile;}
       if(lastep) {print "LAST ENERGY IS POSITIVE (E>0)" >> msgfile; exit 2;}
    }
    '
    RETURNCODE="$?"

    echo "OSZICAR_CHECKER END" >> "$MSGFILE"

    return "$RETURNCODE"
}




function VASP_OUTCAR_CHECKER {
    local MSGFILE="$1"
    local EXITPID="$2"

    echo "OUTCAR_CHECKER ACTIVE" > "$MSGFILE"
    # Now we can follow the OUTCAR
    HT_TASK_FOLLOW_FILE OUTCAR "$EXITPID" | awk -v"msgfile=$MSGFILE" '
    /^ *total allocation   :    [0-9.]* KBytes/ {
          if($3 > 500000) {
            print "REALSPACEALLOCTOOLARGE" >> msgfile;
            exit 2;
          }
       }
    /^ *General timing and accounting informations for this job: *$/ {
       print "FINISHED" >> msgfile;
    }
    '
    RETURNCODE="$?"

    echo "OUTCAR_CHECKER END" >> "$MSGFILE"

    return "$RETURNCODE"
}





#Timeouts: 1 year=31536000, 1 week=604800, 1 day=86400, 6h=21600
function VASP_RUN_CONTROLLED {
    TIMEOUT="$1"
    shift 1
    COMMAND="$1"
    shift 1
    HT_TASK_RUN_CONTROLLED "$TIMEOUT" VASP_STDOUT_CHECKER VASP_OSZICAR_CHECKER VASP_OUTCAR_CHECKER -- "$COMMAND" "$@"
    RETURNCODE="$?"
    echo "$(date) EXIT STATUS=$RETURNCODE"
    if [ "$RETURNCODE" == "100" ]; then
	echo "$(date): VASP APPEAR TO HAVE STOPPED DUE TO USER SIGNAL (SIGINT), PUT JOB IN BROKEN STATE."
	HT_TASK_BROKEN
    fi
    if [ "$RETURNCODE" == "0" ]; then
	if grep "^FINISHED" ht.controlled.msgs; then
	    echo "$(date): VASP APPEAR TO HAVE STOPPED NORMALLY."
	else
	    echo "$(date): VASP APPEAR TO HAVE HALTED ** WITH AN ERROR **."
	    RETURNCODE=2
	fi
	if grep "^LAST BADCONV" ht.controlled.msgs; then
	    echo "CONVERGENCE PROBLEM IN LAST IONIC STEP."
	    RETURNCODE=4
	fi
    fi
    mv stdout.out vasp.out

    return "$RETURNCODE"
}

function VASP_INPUTS_ADJUST {
    # Assumes we are inside an atomic section
    #
    echo "========= VASP ADJUSTMENT BASED ON ========"
    echo "============ ht.controlled.msgs ==========="
    cat ../ht.controlled.msgs | sort | uniq
    echo "==========================================="

    ANYREMEDY=0
    if grep "^KPTSCLASS*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "KPOINT CLASS WARNING DETECTED"
	PROBLEM="kptsclass"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	echo "KPOINT CLASS PROBLEM REMEDYSTEP: $REMEDYSTEP"
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="BUMP_KPTS"
		;;
	    1)
		ANYREMEDY=1
		REMEDY="GAMMA_KPTS"
		;;
	    2)
		ANYREMEDY=1
		REMEDY="BUMP_KPTS\nGAMMA_KPTS"
		;;
	    3)
		ANYREMEDY=1
		REMEDY="EQUAL_KPTS"
		;;
	    4)
		ANYREMEDY=1
		REMEDY="BUMP_KPTS\nEQUAL_KPTS"
		;;
	    5)
		ANYREMEDY=1
		REMEDY="NOSYM"
		;;
	    6)
		ANYREMEDY=1
		REMEDY="NOSYM\nEQUAL_KPTS"
		;;
	    *)
		REMEDY="BUMP_KPTS\nEQUAL_KPTS"
		echo "NO MORE IDEAS FOR $PROBLEM"
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^DENTET*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "DENTET WARNING DETECTED"
	PROBLEM="dentet"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="GAUSSMEAR"
		;;
	    1)
		ANYREMEDY=1
		REMEDY="BUMP_KPTS"
		;;
	    2)
		ANYREMEDY=1
		REMEDY="BUMP_KPTS\nGAMMA_KPTS"
		;;
	    3)
		ANYREMEDY=1
		REMEDY="BUMP_NEDOS"
		;;
	    *)
		REMEDY="BUMP_NEDOS"
		echo "NO MORE IDEAS FOR $PROBLEM"
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^SHIFTS*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "COULD NOT GET CORRECT SHIFTS WARNING"
	PROBLEM="shifts"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="GAMMA_KPTS"
		;;
	    *)
		REMEDY="GAMMA_KPTS"
		echo "NO MORE IDEAS FOR $PROBLEM"
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^LREALFALSE*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "VASP ASKS TO BE RESTARTED WITH LREAL=.FALSE."
	PROBLEM="lreal"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="LREALFALSE"
		;;
	    *)
		REMEDY="LREALFALSE"
		echo "NO MORE IDEAS FOR $PROBLEM"
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^INVROTMATRIX*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "PROBLEM WITH FINDING INVERESE ROTATION MATRIX WARNING"
	PROBLEM="tetkpts"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="NOSYM"
		;;
	    *)
		REMEDY="NOSYM"
		echo "NO MORE IDEAS FOR $PROBLEM"
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^LAST BADCONV ION" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "PROBLEM: BAD ION RELAXATION CONVERGENCE."
	PROBLEM="ionrelax"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		if grep "^FINISHED*" ../ht.controlled.msgs >/dev/null 2>&1; then
		    echo "RETRYING RELAXATION STEP, STARTING FROM LAST POSITION"
		    cp ../CONTCAR POSCAR
		    ANYREMEDY=1
		else
		    # Give up!
		    echo "RUN DID NOT FINISH, SO, NO CONTCAR TO CONTINUE FROM"
		    echo "NO MORE IDEAS FOR $PROBLEM"
		fi
		;;
	    *)
		echo "NO MORE IDEAS FOR $PROBLEM"
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^LAST BADCONV ELEC" ../ht.controlled.msgs >/dev/null 2>&1 || grep "^FEXCF" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "PROBLEM: BAD ELECTRONIC RELAXATION CONVERGENCE."
	PROBLEM="elecrelax"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="SOFTMIX"
		;;
	    1)
		ANYREMEDY=1
		REMEDY="SOFTMIX2"
		;;
	    2)
		ANYREMEDY=1
		REMEDY="ALGOALL"
		;;
	    3)
		ANYREMEDY=1
		REMEDY="ALGOALL2"
		;;
	    4)
		ANYREMEDY=1
		REMEDY="ALGODAMPED"
		;;
	    *)
		REMEDY="ALGODAMPED"
		echo "NO MORE IDEAS FOR $PROBLEM"
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi
}

function VASP_INPUTS_FIX_ERROR {

    #############################################
    #                                           #
    #  Assumes we are inside an atomic section  #
    #  Returns 3 for give up                    #
    #  Returns 2 for cell is too small          #
    #  Returns 0 for all is well, continue      #
    #                                           #
    #############################################

    echo "========= VASP PROBLEM DETECTED ========"
    echo "========== ht.controlled.msgs =========="
    cat ../ht.controlled.msgs | sort | uniq
    echo "========================================"

    ANYREMEDY=0

    RETURNCODE=0

    if grep "^PRICELL*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "PRICELL PROBLEM DETECTED."
	PROBLEM="pricell"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="LOWSYMPREC"
		;;
	    1)
		ANYREMEDY=1
		REMEDY="HIGHSYMPREC"
		;;
	    2)
		ANYREMEDY=1
		REMEDY="NOSYM"
		;;
	    *)
		# Give up!
		echo "GIVING UP"
		return 3
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi


    if grep "^ZPOTRF*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "ZPOTRF PROBLEM DETECTED."
	PROBLEM="zpotrf"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	echo "ZPOTRF REMEDYSTEP: $REMEDYSTEP"
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		RETURNCODE=2
		;;
	    1)
		ANYREMEDY=1
		REMEDY="BUMP_KPTS"
		;;
	    2)
		ANYREMEDY=1
		REMEDY="BUMP_BANDS"
		;;
	    3)
		ANYREMEDY=1
		REMEDY="GAUSSMEAR"
		;;
	    4)
		ANYREMEDY=1
		REMEDY="NOSYM"
		;;
	    *)
		# Give up!
		echo "GIVING UP"
		return 3
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^TETKPTS*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "PROBLEM WITH TETRAHEDRON KPOINT METHOD DETECTED"
	PROBLEM="tetkpts"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="GAUSSMEAR"
		;;
	    *)
		# Give up!
		echo "GIVING UP"
		return 3
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^ZBRENT_BRACKETING*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "PROBLEM WITH ZBRENT BRACKETING"
	PROBLEM="zbrentbracketing"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="EDIFF_SMALLER"
		;;
	    1)
		ANYREMEDY=1
		REMEDY="EDIFF_SMALLER_2"
		;;
	    *)
		# Give up!
		echo "GIVING UP"
		return 3
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^REAL_OPTLAY*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "REAL_OPTLAY ERROR."
	PROBLEM="lrealoptlay"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    0)
		ANYREMEDY=1
		REMEDY="LREALFALSE"
		;;
	    *)
		# Give up!
		echo "GIVING UP"
		return 3
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^TOOCLOSE*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "PROBLEM: IONS TOO CLOSE."
	PROBLEM="tooclose"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    *)
		ANYREMEDY=1
		RETURNCODE=2
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    if grep "^NONLR_ALLOC*" ../ht.controlled.msgs >/dev/null 2>&1; then
	echo "NONLR_ALLOC PROBLEM; OFTEN LEADING TO VASP ALLOCATING ALL AVAILABLE MEMORY."
	PROBLEM="nonlralloc"
	if [ -e "../ht.remedy.$PROBLEM" ]; then
	    REMEDYSTEP=$(cat "../ht.remedy.$PROBLEM" | awk 'NR==1 {print $0}')
	    REMEDYSTEP=$((REMEDYSTEP+1))
	else
	    REMEDYSTEP=0
	fi
	case "$REMEDYSTEP" in
	    *)
		# Give up!
		echo "GIVING UP"
		return 3
		;;
	esac
	echo -e "$REMEDYSTEP\n$REMEDY" >> "ht.remedy.$PROBLEM"
    fi

    # If we didn't find anything to do, lets try this as well
    if [ "$ANYREMEDY" == "0" ]; then
	VASP_INPUTS_ADJUST
    fi

    # If we still didn't find anything to do, we need to give up
    if [ "$ANYREMEDY" == "0" ]; then
	echo "UNKNOWN PROBLEM. GIVING UP."
	return 3
    fi

    return "$RETURNCODE"
}

function VASP_SET_TAG {
    TAG="$1"
    VALUE="$2"
    (awk "!/^ *$TAG *=/{print \$0}" INCAR; echo "$TAG=$VALUE") > ht.tmp.INCAR
    mv ht.tmp.INCAR INCAR
}




function VASP_GET_TAG {
    TAG="$1"
    if [ -z "$2" ]; then
	FILE="INCAR"
    else
	FILE="$2"
    fi
    awk -F= "/^ *$TAG *=/{print \$2}" $FILE
}

function VASP_GET_VOLUME {
    local FILE
    if [ -z "$1" ]; then
	FILE=./vasprun.xml
    else
	FILE="$1"
    fi
    grep "<i name=\"volume\">" "$FILE" | tail -n 1 | sed -n 's/^.*<i name="volume"> *\([0-9.]*\) *<\/i>.*$/\1/p'
}

function VASP_GET_ENERGY {
    local FILE
    if [ -z "$1" ]; then
	FILE=./OSZICAR
    else
	FILE="$1"
    fi
    grep "E0=" "$FILE" | tail -1 | sed -n -e 's/^.*E0= \([-0-9.E+]*\).*$/\1/p'
}

function VASP_RATTLE_POSCAR {
    awk '
    FNR>=3 && FNR<=5 {
      printf("%.14f %.14f %.14f\n",$1+rand()*0.1 - 0.1/2.0,$2+rand()*0.1 - 0.1/2.0,$3+rand()*0.1 - 0.1/2.0);
      next
    }
    FNR>=8 && NF == 3 {
      printf("%.14f %.14f %.14f\n",$1+rand()*0.1 - 0.1/2.0 , $2+rand()*0.1 - 0.1/2.0 , $3+rand()*0.01 - 0.1/2.0);
     next
   }
   {
     print $0
   }
' POSCAR > ht.tmp.POSCAR
mv ht.tmp.POSCAR POSCAR
}

function VASP_POTCAR_SUMMARY {
    local FILE=$1
    if [ -z "$FILE" ]; then
	FILE=POTCAR
    fi
    awk '
    /^ *parameters from PSCTR are:/ {print keep2, keep1, on=1}
    /^ *Description/ {on=0}
    {keep2=keep1; keep1=$0}
     on==1 {print $0}
    ' "$FILE" > POTCAR.summary
}

# Vasp cuts the first line in the CONTCAR, this fixes that problem
function VASP_CONTCAR_TO_POSCAR {
    local CONTCAR="$1"
    if [ -z "$CONTCAR" ]; then
	CONTCAR="CONTCAR"
    fi
    local REFPOSCAR="$2"
    if [ -z "$REFPOSCAR" ]; then
	REFPOSCAR="POSCAR"
    fi
    FIRSTLINE=$(head -n 1 "$REFPOSCAR")
    (echo "$FIRSTLINE"; awk 'NR==1 {next} {print $0}' "$CONTCAR") > POSCAR
}

function VASP_CLEAN_OUTCAR {
    local FILE=$1
    if [ -z "$FILE" ]; then
	FILE=OUTCAR
    fi
    if [ ! -e "$FILE" ]; then
	echo "VASP_CLEAN_OUTCAR: Missing $FILE file." >&2
	exit 1
    fi
    awk '
    /^ *k-point *[0-9*]* *: +[0-9.-]* +[0-9.-]* +[0-9.-]* *$/ && off==0 {print "VASP_CLEAN_OUTCAR: Removed k-point occupation data"; off=1}
    /^ *k-points in units of 2pi\/SCALE and weight:/ && off==0 {print "VASP_CLEAN_OUTCAR: Removed k-point listning."; off=2}
    /^ *Following reciprocal coordinates:/ && off==0 {print "VASP_CLEAN_OUTCAR: Removed k-point specification"; off=2}
    /^ *Following cartesian coordinates:/ && off==0 {print "VASP_CLEAN_OUTCAR: Removed k-point specification"; off=2}
    /^ *k-points in reciprocal lattice and weights/ && off==0 {print "VASP_CLEAN_OUTCAR: Removed k-point specification"; off=2}
    /^ *k-point +[0-9*]* .* plane waves/ && off==0 {print "VASP_CLEAN_OUTCAR: Removed k-point plane wave data"; off=2}
    off==1 && /^ *----------------------------------- */{off=0}
    off==2 && /^ *$/{off=0}
    off==0 {print $0}
    ' "$FILE" > OUTCAR.cleaned
}
