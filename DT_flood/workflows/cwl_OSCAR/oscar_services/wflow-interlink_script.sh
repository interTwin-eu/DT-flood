FILE_NAME=`basename "$INPUT_FILE_PATH"`
ID=`basename "$INPUT_FILE_PATH" | cut -d'_' -f1`
OUTPUT_FILE="$TMP_OUTPUT_DIR"/"$ID"_wflow_output.tar
mkdir -p /tmp/model
tar -xvf  "$INPUT_FILE_PATH" -C /tmp/model/
/app/build/create_binaries/wflow_bundle/bin/wflow_cli /tmp/model/wflow_warmup/wflow_sbm.toml
tar -cf /tmp/wflow_output.tar /tmp/model/wflow_warmup/run_default/
mv /tmp/wflow_output.tar  $OUTPUT_FILE