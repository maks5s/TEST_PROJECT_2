# TEST_PROJECT_2

## Requirements

### Operating System
- Any Linux distribution of your choice
- WSL (Windows Subsystem for Linux)

### Python
- Python 2.7.13

## Environment Setup

To run this project, follow these steps:

1. **Install pyenv**
   - Follow the installation instructions at: https://github.com/pyenv/pyenv#installation

2. **Install pyenv-virtualenv plugin**
   - Follow the installation instructions at: https://github.com/pyenv/pyenv-virtualenv#installation

3. **Install Python 2.7.13 using pyenv**
   ```bash
   pyenv install 2.7.13
   ```

4. **Create a virtual environment based on Python 2.7.13**
   - Instructions available at: https://github.com/pyenv/pyenv-virtualenv#usage
   ```bash
   pyenv virtualenv 2.7.13 test_project_2_env
   ```

5. **Activate the virtual environment**
   ```bash
   pyenv activate test_project_2_env
   ```

6. **Install project dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

```
alembic/          - Directory containing migration files
data/             - Directory for storing SQLite databases
logs/             - Directory for storing application logs
models/           - Directory containing SQLAlchemy model code
modules/          - Directory containing Python project modules
queries/          - Directory containing database query code
tests/            - Directory containing test code and fixtures
alembic.ini       - Alembic configuration file
config.yaml       - Project configuration file
.gitignore        - Git ignore file
__init__.py       - Init file
main.py           - Module containing project code and entry point
README.md         - Project description and tasks
requirements.txt  - Project dependencies description
yapf.config       - YAPF configuration file
```

## Tasks

### Running the Project

1. Activate the virtual environment
2. Navigate to the project directory
3. Run the project with the command:
   ```bash
   python main.py
   ```

**Note:** The project will not run successfully on the first attempt as it contains several errors that need to be fixed.

---

### Task Categories

All tasks listed below are divided into **mandatory** and **optional** tasks.
- Optional tasks can be completed in any order and may be skipped.
  ONE TASK FROM THE LIST IS REQUIRED.
- All tasks are listed from easiest to most difficult

---

## Mandatory Tasks.

These tasks involve fixing errors necessary to run the project:

1. **Fix the error described in the log file:**
   - `logs/archive/application_exception_1.log`

2. **Fix the error described in the log file:**
   - `logs/archive/application_exception_2.log`

---

## Optional Tasks


### 1. Add a Simple Flask Web Server

- Add an endpoint that returns a list of active users from the Users table
  - Result should be returned in JSON format
- Add a Postman collection to call this endpoint

### 2. Add Alembic Migration

Create an Alembic migration that includes:

- **Resources table**
  - Resource type and table structure to be defined by the developer
- **Many-to-many relationship** between Users and Resources tables
- **Add Resources model** in `./models/application.py`
- **Run the migration** by adding the necessary code in:
  - `./main.py` if the web server step was skipped
  - In the web server code if the web server was added

### 3. Optimize Project Code

Optimize the code to speed up the execution of `app.get_users(execution_count=100)` (line 207 in `./main.py`)

- **Current result** is described in `logs/archive/application_success.log` (see lines 3777-3778)
  - Approximate value: 14 seconds
- **Expected result** is described in `logs/archive/application_success_expected.log` (see lines 3777-3778)
  - Target value: 10 seconds

---

## Getting Help

If you encounter any issues or have questions about the tasks, please refer to the log files in the `logs/archive/` directory for detailed error information and execution results.