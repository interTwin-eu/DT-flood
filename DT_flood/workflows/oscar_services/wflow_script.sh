FILE_NAME=`basename "$INPUT_FILE_PATH"`
ID=`basename "$INPUT_FILE_PATH" | cut -d'_' -f1`
OUTPUT_FILE="$TMP_OUTPUT_DIR"/"$ID"_wflow_output.tar
echo $OUTPUT_FILE
mkdir -p model
tar -xvf  "$INPUT_FILE_PATH" -C model/
/app/build/create_binaries/wflow_bundle/bin/wflow_cli model/wflow_sbm.toml
tar -cf wflow_output.tar model/
mv wflow_output.tar  $OUTPUT_FILE
