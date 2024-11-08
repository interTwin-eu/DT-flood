FILE_NAME=`basename "$INPUT_FILE_PATH"`
OUTPUT_FILE="$TMP_OUTPUT_DIR/wflow_output.tar"
mkdir -p /model
tar -xvf  "$INPUT_FILE_PATH" -C /model/
/app/build/create_binaries/wflow_bundle/bin/wflow_cli /model/wflow_warmup/wflow_sbm.toml
tar -cf wflow_output.tar /model/wflow_event/instate/instates.nc
mv wflow_output.tar  $OUTPUT_FILE
