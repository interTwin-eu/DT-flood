ID=`basename "$INPUT_FILE_PATH" | cut -d'_' -f1`
OUTPUT_FILE="$TMP_OUTPUT_DIR"/"$ID"_ra2ce_output.tar
echo $OUTPUT_FILE
mkdir -p data
tar -xvf "$INPUT_FILE_PATH" -C data/
python3 /ra2ce_src/ra2ce/__main__.py --network_ini $(pwd)/data/network.ini --analyses_ini $(pwd)/data/analysis.ini
tar -cf ra2ce_output.tar data/
mv ra2ce_output.tar $OUTPUT_FILE