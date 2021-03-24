#!/usr/bin/bash

# This script can be used used to run all examples, tutorials and tests to make sure
# everything works on both Python 2 and 3.

# pyenv is used to switch between python 2 and 3 versions, so
# pyenv and the pyenv-virtualenv plugin must be installed
# in order to this script to work.

if ! command -v pyenv &> /dev/null
then
    echo "pyenv needs to be installed before running this script!"
    exit
fi

# NOTE: Starting with bash version 4, both stdout and stderr can be redirected
# to the same file using `cmd &>> file.txt` construct.

# If one wants to see the output in the terminal as well as copy it to a file,
# a pattern "command |& tee -a out.file" will accomplish this.

# The following snippet saves this script's home folder to SCRIPT_DIR, no matter where
# the script is called from. Useful for copying files from the script folder to
# somewhere else.
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$SCRIPT_DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

HTTK_DIR=${HOME}/httk
OUT_FILE=${HTTK_DIR}/Tests/TEST.out

echo "############ Testing starts ############" |& tee $SCRIPT_DIR/$OUT_FILE

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
for version in "2.7.18" "3.7.10"
do

cd $HTTK_DIR
# Make sure pytest doesn't pick up unwanted .py files for testing:
make clean

if [ $version == "2.7.18" ]; then
    export TEST_EXPECT_PYVER=2
    pyver=2
    echo "############ Python 2 ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
else
    export TEST_EXPECT_PYVER=3
    pyver=3
    echo "############ Python 3 ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
fi

pyenv install -s $version
pyenv virtualenv $version httk_test_$version
pyenv activate httk_test_$version
pip install -r $HTTK_DIR/py${pyver}7requirements.txt
# Optional dependencies:
if [ $version == "3.7.10" ]; then
    pip install duckdb
fi

CURRENT_VERSION="$(python -V 2>&1)"
echo "Current Python version: $CURRENT_VERSION" |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: unittests ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
make unittests |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: pytest ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
make pytest |& tee -a $SCRIPT_DIR/$OUT_FILE

#echo "############ Python $pyver: tox ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
#rm -r .tox; make tox |& tee -a $SCRIPT_DIR/$OUT_FILE

cp -r Examples tmp_Examples
cp -r Tutorial tmp_Tutorial
cp $SCRIPT_DIR/required_files/example.sqlite tmp_Tutorial/Step6
#cp -r $SCRIPT_DIR/required_files/poscar tmp_Tutorial/

##################################################################################################
# Examples
##################################################################################################

cd $HTTK_DIR/tmp_Examples/0_import_httk
echo "############ Python $pyver: Examples/0_import_httk/0_import_httk.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 0_import_httk.py |& tee -a $SCRIPT_DIR/$OUT_FILE

cd $HTTK_DIR/tmp_Examples/1_simple_things
echo "############ Python $pyver: Examples/1_simple_things/0_vectors.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 0_vectors.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/1_simple_things/1_structure.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 1_structure.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/1_simple_things/2_build_supercell.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 2_build_supercell.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep "java.*jmol" | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait

echo "############ Python $pyver: Examples/1_simple_things/3_read_cif.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 3_read_cif.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/1_simple_things/4_read_poscar.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 4_read_poscar.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/1_simple_things/5_write_poscar.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 5_write_poscar.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/1_simple_things/6_write_cif.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 6_write_cif.py |& tee -a $SCRIPT_DIR/$OUT_FILE

cd $HTTK_DIR/tmp_Examples/2_visualization
echo "############ Python $pyver: Examples/2_visualization/1_structure_visualizer.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 1_structure_visualizer.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep "java.*jmol" | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait

echo "############ Python $pyver: Examples/2_visualization/2_ase_visualizer.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 2_ase_visualizer.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep "ase gui" | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait

cd $HTTK_DIR/tmp_Examples/3_external_libraries
echo "############ Python $pyver: Examples/3_external_libraries/1_ase_structure_conversion.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 1_ase_structure_conversion.py |& tee -a $SCRIPT_DIR/$OUT_FILE

## The next example requires the API key to be set:
echo "############ Python $pyver: Examples/3_external_libraries/2_phasediagram_from_materialsproject.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
sed -i 's/xxxxxx/${MATPROJ_API_KEY}/' 2_phasediagram_from_materialsproject.py
python 2_phasediagram_from_materialsproject.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep 2_phasediagram | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait


# The third example references the example.sqlite file in the Step6 tutorial:
echo "############ Python $pyver: Examples/3_external_libraries/3_phasediagram_pymatgen.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
#sed -i 's/Tutorial\/Step6/tmp_Tutorial\/Step6/g' 3_phasediagram_pymatgen.py
python 3_phasediagram_pymatgen.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep 3_phasediagram | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait

cd $HTTK_DIR/tmp_Examples/4_database
echo "############ Python $pyver: Examples/4_database/1_store_retrieve.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
sed -i 's/Tutorial\/Step7/tmp_Tutorial\/Step7/g' 1_store_retrieve.py
python 1_store_retrieve.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/4_database/2_own_data.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
sed -i 's/Tutorial\/Step7/tmp_Tutorial\/Step7/g' 2_own_data.py
python 2_own_data.py |& tee -a $SCRIPT_DIR/$OUT_FILE

## In sed, if we substitute using a bash variable that contains a slash, e.g.
## url or folder path, we have to change the sed separator to "|".
cd $HTTK_DIR/tmp_Examples/5_calculations
echo "############ Python $pyver: Examples/5_calculations/1_simple_vasp.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
#sed -i "s|poscarspath = None|poscarspath = \"$HTTK_DIR\/tmp_Tutorial\/poscar\"|g" 1_simple_vasp.py
python 1_simple_vasp.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/5_calculations/2_ht_vasp.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
sed -i 's/Tutorial/tmp_Tutorial/' 2_ht_vasp.py
#sed -i "s|^poscarspath = .*$|poscarspath = \"$HTTK_DIR\/tmp_Tutorial\/poscar\"|" 2_ht_vasp.py
python 2_ht_vasp.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/6_website NOT IMPLEMENTED YET! ############" |& tee -a $SCRIPT_DIR/$OUT_FILE

cd $HTTK_DIR/tmp_Examples/8_elastic_constants
echo "############ Python $pyver: Examples/8_elastic_constants/1_generate_Runs.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 1_generate_Runs.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/8_elastic_constants/4_make_database.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 4_make_database.py |& tee -a $SCRIPT_DIR/$OUT_FILE

cd $HTTK_DIR/tmp_Examples/9_duckdb
echo "############ Python $pyver: Examples/9_duckdb/1_make_duckdb_database.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 1_make_duckdb_database.py |& tee -a $SCRIPT_DIR/$OUT_FILE

echo "############ Python $pyver: Examples/9_duckdb/4_analyze_database_using_python.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python 4_analyze_database_using_python.py |& tee -a $SCRIPT_DIR/$OUT_FILE




##################################################################################################
# Tutorials
##################################################################################################

cd $HTTK_DIR/tmp_Tutorial/Step1
echo "############ Python $pyver: Tutorial/Step1/step1.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step1.py |& tee -a $SCRIPT_DIR/$OUT_FILE

cd $HTTK_DIR/tmp_Tutorial/Step2
echo "############ Python $pyver: Tutorial/Step2/step2.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step2.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep "java.*jmol" | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait

echo "############ Python $pyver: Tutorial/Step2/step2_part2.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step2_part2.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep "java.*jmol" | grep -v grep | awk '{print $2}'`
    ## After the main jmol window is killed, the dialog box with the OK button
    ## still has to be killed. This process is defunct, so there is an extra
    ## step in killing it.
    dialogpid=`ps -ef | grep "\[jmol\] <defunct>" | grep -v grep | awk '{print $2}'`
    dialogparentpid=`ps -ef | grep "\[jmol\] <defunct>" | grep -v grep | awk '{print $3}'`
    if [ "$killpid" == "" ]; then
	if [ "$dialogpid" == "" ]; then
	    break
	else
	    kill -9 $dialogpid $dialogparentpid
	fi
    else
	kill $killpid
    fi
done
wait

cd $HTTK_DIR/tmp_Tutorial/Step3
echo "############ Python $pyver: Tutorial/Step3/step3.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step3.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 30
    killpid=`ps aux | grep "java.*jmol" | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait

cd $HTTK_DIR/tmp_Tutorial/Step4
echo "############ Python $pyver: Tutorial/Step4/step4.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step4.py |& tee -a $SCRIPT_DIR/$OUT_FILE

cd $HTTK_DIR/tmp_Tutorial/Step5
echo "############ Python $pyver: Tutorial/Step5/step5.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
#sed -i "s|poscarspath = None|poscarspath = \"$HTTK_DIR\/tmp_Tutorial\/poscar\"|g" step5.py
python step5.py |& tee -a $SCRIPT_DIR/$OUT_FILE

cd $HTTK_DIR/tmp_Tutorial/Step6
echo "############ Python $pyver: Tutorial/Step6/step6_part1.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
#sed -i "s|poscarspath = None|poscarspath = \"$HTTK_DIR\/tmp_Tutorial\/poscar\"|g" step6_part1.py
python step6_part1.py |& tee -a $SCRIPT_DIR/$OUT_FILE
rm -r Runs
unzip $SCRIPT_DIR/required_files/Step6_Runs.zip
cp -r $SCRIPT_DIR/required_files/ht.project .
echo "############ Python $pyver: Tutorial/Step6/step6_part4.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step6_part4.py |& tee -a $SCRIPT_DIR/$OUT_FILE
echo "############ Python $pyver: Tutorial/Step6/step6_part5.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step6_part5.py |& tee -a $SCRIPT_DIR/$OUT_FILE &
while :
do
    sleep 60
    killpid=`ps aux | grep step6_part5 | grep -v grep | awk '{print $2}'`
    if [ "$killpid" == "" ]; then
	break
    else
	kill $killpid
    fi
done
wait

cd $HTTK_DIR/tmp_Tutorial/Step7
echo "############ Python $pyver: Tutorial/Step7/step7.py ############" |& tee -a $SCRIPT_DIR/$OUT_FILE
python step7.py |& tee -a $SCRIPT_DIR/$OUT_FILE

# clean up
cd $HTTK_DIR
rm -r tmp_Examples
rm -r tmp_Tutorial
pyenv deactivate httk_test_$version
pyenv virtualenv-delete -f httk_test_$version
done
