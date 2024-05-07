# Speckle Automate Workshop: Python Function Template

This repository serves as a starting point for creating Speckle Automate
functions in Python for the Automate workshops.
It is based on
the [Speckle Automate Python Function Template](https://github.com/specklesystems/speckle_automate_python_example)
which
is the preferred starting point for creating new
Speckle Automate functions in Python.

## Getting started

This template will be available from the Speckle Automate New Function wizard.
Select the Workshop icon to create a new repository from this template.

By default, the wizard will create a new repository in your GitHub account,
and you will be able to start editing the code in the `main.py` file.

To create a new version of your Function, create a new GitHub release in your
repository.
This will trigger GitHub Action that builds, tests and deploys your function to
Speckle Automate.

### Managing Dependencies with Poetry

Poetry simplifies dependency management for Python projects, ensuring consistent
environments and hassle-free dependency
resolution. Here's why we use Poetry:

Dependency Resolution: Poetry ensures compatible library versions, preventing
conflicts.
Virtual Environments: It manages project dependencies in isolated virtual
environments.
Lockfile: Generates a lockfile (poetry.lock) for reproducible builds.
Simplified Installation: Adding dependencies is as easy as poetry add <
package-name>.
Dependency Isolation: Ensures project dependencies are self-contained and
portable.
Project Metadata: Manages project configuration in a single `pyproject.toml`
file.

#### Adding Dependencies

To add new dependencies, use:

`$ poetry add <package-name>`

Replace <package-name> with the desired package. Poetry handles the rest,
updating project files automatically.

Note: It's while it is a good practice to combine the use of Poetry with virtual
environments to ensure a clean and
isolated development environment for your Python projects, other tools like
pipenv or venv can also be used. It is not
mandatory to use a virtual environment for Speckle Automate functions.

### Configuring Launch Variables (Visual Studio Code)

To edit launch variables in Visual Studio Code, follow these steps:

Open the project in Visual Studio Code.
Navigate to the .vscode directory.
Open the launch.json file.
Edit the configurations as needed.
Save the file.
These configurations specify how your Python script will be run and debugged
within Visual Studio Code.

### GitHub Codespaces

Once you have created a clone of this template repo with the Automate wizard,
you can use GitHub Codespaces to
develop your function in the cloud. In the Codespaces environment, you can edit
code, run tests, and debug your
function.
To open your repository in a Codespace, click the "Code" button in the GitHub UI
and select "Open with Codespaces".

## Using this Speckle Function

1. [Create](https://automate.speckle.dev/) a new Speckle Automation.
2. Select your Speckle Project and Speckle Model.
3. Select the Speckle Function you created from this template.
4. Enter the requested inputs. For first run this will be a phrase to use in a
   comment.
5. Click `Create Automation`.

## Developer Requirements

1. Install the following:
    - [Python 3](https://www.python.org/downloads/) (>= 3.10)
    - [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
2. Run `poetry shell && poetry install` to install the required Python packages.

## Building and Testing

The code can be tested locally by running `poetry run pytest`. The tests are
located in the `tests` directory.
The tests also allow for testing the function locally by mocking the Speckle
Automate environment or using the specklepy
authentication token to connect to a real Speckle Server and use real data.

### Building and running the Docker Container Image

Running and testing your code on your own machine is a great way to develop your
Function; the following instructions
are a bit more in-depth and only required if you are having issues with your
Function in GitHub Actions or on Speckle
Automate.

#### Building the Docker Container Image

Your code is packaged by the GitHub Action into the format required by Speckle
Automate. This is done by building a
Docker Image, which is then run by Speckle Automate. You can attempt to build
the Docker Image yourself to test the
building process locally.

To build the Docker Container Image, you will need to
have [Docker](https://docs.docker.com/get-docker/) installed.

Once you have Docker running on your local machine:

1. Open a terminal
2. Navigate to the directory in which you cloned this repository
3. 3.Run the following command:

    ```bash
    docker build -f ./Dockerfile -t speckle_automate_python_example .
    ```

#### Running the Docker Container Image

Once the image has been built by the GitHub Action, it is sent to Speckle
Automate. When Speckle Automate runs your
Function as part of an Automation, it will run the Docker Container Image. You
can test that your Docker Container Image
runs correctly by running it locally.

1. To then run the Docker Container Image, run the following command:

    ```bash
    docker run --rm speckle_automate_python_example \
    python -u main.py run \
    '{"projectId": "1234", "modelId": "1234", "branchName": "myBranch", "versionId": "1234", "speckleServerUrl": "https://speckle.xyz", "automationId": "1234", "automationRevisionId": "1234", "automationRunId": "1234", "functionId": "1234", "functionName": "my function", "functionLogo": "base64EncodedPng"}' \
    '{}' \
    yourSpeckleServerAuthenticationToken
    ```

Let's explain this in more detail:

`docker run --rm speckle_automate_python_example` tells Docker to run the Docker
Container Image that we built
earlier. `speckle_automate_python_example` is the name of the Docker Container
Image that we built earlier. The `--rm`
flag tells docker to remove the container after it has finished running, this
frees up space on your machine.

The line `python -u main.py run` is the command that is run inside the Docker
Container Image. The rest of the command
is the arguments that are passed to the command. The arguments are:

- `'{"projectId": "1234", "modelId": "1234", "branchName": "myBranch", "versionId": "1234", "speckleServerUrl": "https://speckle.xyz", "automationId": "1234", "automationRevisionId": "1234", "automationRunId": "1234", "functionId": "1234", "functionName": "my function", "functionLogo": "base64EncodedPng"}'` -
  the metadata that describes the automation and the function.
- `{}` - the input parameters for the function that the Automation creator is
  able to set. Here they are blank, but you
  can add your own parameters to test your function.
- `yourSpeckleServerAuthenticationToken` - the authentication token for the
  Speckle Server that the Automation can
  connect to. This is required to be able to interact with the Speckle Server,
  for example to get data from the Model.

## Resources

- [Learn](https://speckle.guide/dev/python.html) more about `specklepy`, and
  interacting with Speckle from Python.
