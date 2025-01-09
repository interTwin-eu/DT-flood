call mamba env create -n de372_demo -f environment.yml
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
call activate de372_demo
call mamba list hydromt
call pip install dfm_tools earthkit jupyter solara ipyleaflet mapbox-earcut localtileserver html2image
call deactivate