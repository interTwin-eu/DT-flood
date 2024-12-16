ID=`basename "$INPUT_FILE_PATH" | cut -d'_' -f1`
OUTPUT_FILE="$TMP_OUTPUT_DIR"/"$ID"_sfincs_output.tar
echo $OUTPUT_FILE
tar -xvf  "$INPUT_FILE_PATH" -C /data/
sfincs | tee sfincs_log.txt
tar -cf sfincs_output.tar sfincs_map.nc sfincs_his.nc sfincs_log.txt
mv /data/sfincs_output.tar  $OUTPUT_FILE
