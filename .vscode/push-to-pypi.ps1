Remove-Item -ErrorAction SilentlyContinue -Recurse ./dist/*
Remove-Item -ErrorAction SilentlyContinue -Recurse ./build/*
Remove-Item -ErrorAction SilentlyContinue -Recurse -Confirm:$false ./*.egg-info
python setup_xAOD.py sdist bdist_wheel
python setup_xAOD_backend.py sdist bdist_wheel
twine upload dist/*
Remove-Item -ErrorAction SilentlyContinue -Recurse ./dist/*
Remove-Item -ErrorAction SilentlyContinue -Recurse ./build/*
Remove-Item -ErrorAction SilentlyContinue -Recurse -Confirm:$false ./*.egg-info
