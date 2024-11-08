OUTPUT_FILE="$TMP_OUTPUT_DIR/sfincs_output.tar"
mkdir -p /tmp/data/
tar -xvf  "$INPUT_FILE_PATH" -C /tmp/data/
/bin/bash -c "cd /tmp/data/ && sfincs && tar -cf sfincs_output.tar sfincs_map.nc sfincs_his.nc"
mv /tmp/data/sfincs_output.tar  $OUTPUT_FILE
rm /tmp/data/ -r