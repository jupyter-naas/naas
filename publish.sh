rm -rf dist
python3 -m black naas
python3 -m flake8 naas
cz bump --changelog
python3 setup.py sdist
python3 -m twine upload dist/* -u bobapp
git push origin --tags