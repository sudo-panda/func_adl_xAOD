if(Test-Path -Path dist ){
  Remove-Item dist
}

python setup.py sdist bdist_wheel
twine upload dist/*
