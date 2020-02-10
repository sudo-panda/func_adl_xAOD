if(Test-Path -Path dist ){
  Remove-Item -Force -Recurse dist
}
if (Test-Path -Path build) {
  Remove-Item -Force -Recurse build
}
if (Test-Path -Path .\*.egg-info) {
  Remove-Item -Force -Recurse .\*.egg-info
}

python setup_xAOD.py sdist bdist_wheel
python setup_xAOD_backend.py sdist bdist_wheel
twine upload dist/*
if(Test-Path -Path dist ){
  Remove-Item -Force -Recurse dist
}
if (Test-Path -Path build) {
  Remove-Item -Force -Recurse build
}
if (Test-Path -Path .\*.egg-info) {
  Remove-Item -Force -Recurse .\*.egg-info
}
