OUTPUT_FILE="$TMP_OUTPUT_DIR/sfincs_output.tar"
tar -xvf  "$INPUT_FILE_PATH" -C /data/
sfincs
tar -cf sfincs_output.tar sfincs_map.nc sfincs_his.nc sfincs.log
mv /data/sfincs_output.tar  $OUTPUT_FILE
