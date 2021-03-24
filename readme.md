# unimelb-SWEN90013Backend

## back-end deploy method

###require python3.7 or higher and MySQL

1. Install all packages needed `pip install -r requirements.txt` (if python2 and python3 are both installed, use pip3 and python3)
2. start MySQL server on localhost:3306, and create a database named "sp90013" `CREATE DATABASE sp90013`
3. modify the MySQL username and password config in TeamSPBackend/Settings/dev.py and TeamSPBackend/Settings/prod.py (don't forget to modify 'DATABASES/default/TEST/PASSWORD' in prod.py)
4. create MySQL tables `python manage.py migrate`
5. start server `python manage.py runserver`
6. api web server is now running on: http://127.0.0.1:8000/api/v1
7. to test if the config is set correctly, use `python TeamSPBackend/test/test_case/test_deploy.py`