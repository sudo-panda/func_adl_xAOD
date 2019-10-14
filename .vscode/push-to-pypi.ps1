if(Test-Path -Path dist ){
  Remove-Item -Force -Recurse dist
}

python setup.py sdist bdist_wheel
twine upload dist/*
