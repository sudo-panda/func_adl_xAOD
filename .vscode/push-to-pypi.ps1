if(Test-Path -Path dist ){
  Remove-Item -Force -Recurse dist
}

python setup_xAOD.py sdist bdist_wheel
python setup_xAOD_backend.py sdist bdist_wheel
twine upload dist/*
