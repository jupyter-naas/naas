# Naas (Notebooks As Automated Services)

Schedule notebooks, to automate all your tasks.

Use the power of scripting in the cloud.
Whenever you need it (even when you sleep).

* Schedule your scripts
* Use Notebooks as API
* Share assets securely

# Install

`pip3 install -r requirements.txt`

# Run test 

`pytest -x`  

# test runner

remove uvloop to allow papermill to work
`pip3 uninstall uvloop`

`pytest -x tests/test_runner.py `
or
`./test_runner.sh`

open manager :

`localhost:5000/`