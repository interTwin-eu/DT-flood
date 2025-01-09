ID=`basename "$INPUT_FILE_PATH" | cut -d'_' -f1`
OUTPUT_FILE="$TMP_OUTPUT_DIR"/"$ID"_sfincs_output.tar
mkdir -p /tmp/data/
tar -xvf  "$INPUT_FILE_PATH" -C /tmp/data/
/bin/bash -c "cd /tmp/data/ && sfincs && tar -cf sfincs_output.tar sfincs_map.nc sfincs_his.nc sfincs.log"
mv /tmp/data/sfincs_output.tar  $OUTPUT_FILE
rm /tmp/data/ -r