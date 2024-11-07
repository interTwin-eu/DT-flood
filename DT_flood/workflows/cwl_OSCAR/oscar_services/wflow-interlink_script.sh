FILE_NAME=`basename "$INPUT_FILE_PATH"`
OUTPUT_FILE="$TMP_OUTPUT_DIR/$FILE_NAME.nc"
mkdir -p /tmp/model
tar -xvf  "$INPUT_FILE_PATH" -C /tmp/model/
/app/build/create_binaries/wflow_bundle/bin/wflow_cli /tmp/model/wflow_warmup/wflow_sbm.toml
mv /tmp/model/wflow_event/instate/instates.nc  $OUTPUT_FILE
