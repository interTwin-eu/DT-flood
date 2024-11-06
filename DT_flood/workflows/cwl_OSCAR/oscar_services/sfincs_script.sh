FILE_NAME=`basename "$INPUT_FILE_PATH"`
OUTPUT_FILE="$TMP_OUTPUT_DIR/$FILE_NAME.nc"
mkdir -p /model
tar -xvf  "$INPUT_FILE_PATH" -C /model/
/app/build/create_binaries/wflow_bundle/bin/wflow_cli /model/wflow_warmup/wflow_sbm.toml
mv /model/wflow_event/instate/instates.nc  $OUTPUT_FILE


tar -xvf  "$INPUT_FILE_PATH" -C /data/
sfincs