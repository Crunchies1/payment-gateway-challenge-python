# My notes

I've separated out my backend service into a few different layers:
- Handlers (responsible for the HTTP request/response layer)
- Services (responsible for business logic)
- Clients (responsible for interacting with third party APIs)
- Models (responsible for interacting with the DB)

I didn't implement an actual DB since the root README.md said we didn't need to, but I would have just spun up a docker
container with some mySQL instance if I did. Would then use a DB library to help connect to it. Would then implement
some form of BEGIN TRANSACTION functionality so we keep certain call sequences atomic. Also need isolation somehow as
I think it's possible that a race condition could occur in the code as it is currently.

I created some unit tests to try and cover most of the cases. The most detail went to the payment service as it was the focus point
of the exercise. Made sure to mock almost all other interactions in the unit tests. The integration test involves the full
backend except for third parties, I would involve a test DB instance if we had one, instead of this in-memory list.

I've added dotenv to the project requirements since I would usually put the URLs to these third party API's in an env file, as
if they are updated they usually increment their version suffix like v2 -> v3 and we can just update that in the env file.

Logging/errors is pretty barebones and if it was a real production system, there'd probably be some sort of bubbling up of the logs and have
something capture them to log them on something like GCP. We'd also probably do more proper separation, I've left some consts in the files
which may not be best practice.

There is a card service, it's something extra and I've tried to go over my rationale for it in this whiteboarding
file: https://excalidraw.com/#json=NU2IHTRDH3TsKTFfYOcuH,VwX4OGyfvPUZn1n2VnNo0A

# How to run the app

## Locally

Make sure the following are installed:
- Python 3.12.10
- Poetry

The following command can be used to install Poetry on most operating systems (Linux, macOS, Windows (WSL))
```
curl -sSL https://install.python-poetry.org | python3 -
```

There is a Makefile provided which just runs Poetry under the hood.
```
make install
```

Run the app.
```
make run
```

Run the bank simulator.
```
docker-compose up
```

## Via Docker

Make sure you have Docker installed.

Run the app, force a build to get latest changes.
```
docker compose --profile app up --build
```

# Installing new dependencies

In order to install new dependencies and run them via Poetry, make sure you follow this process:

Add a new dependency.
```
poetry add <package>
```

Install the dependencies.
```
poetry install
```

Move the poetry dependencies into a requirements.txt file. This is
so we can build the Docker image correctly.
```
poetry run pip freeze | grep -v "^-e" > requirements.txt
```

# Running tests

Unit tests: `make test-unit`
Integration tests: `make test-integration`
All tests: `make test`

# Instructions for candidates

This is the Python version of the Payment Gateway challenge. If you haven't already read the [README.md](https://github.com/cko-recruitment) in the root of this organisation, please do so now. 

## Template structure
```
├── .editorconfig - don't change this. It ensures a consistent set of rules for submissions when reformatting code
├── .env.example
├── .python-version - Python version used by Pyenv (https://github.com/pyenv/pyenv).
├── Makefile - Makefile with commands such as install, run and test
├── docker-compose.yml - configures the bank simulator
├── pyproject.toml - project metadata, build system and dependencies
├── poetry.lock - Poetry lock file
├── main.py - app's entrypoint
├── payment_gateway_api/ - skeleton FastAPI API
├── imposters/ - contains the bank simulator configuration. Don't change this
└── tests/ - folder for tests
```

Feel free to change the structure of the solution, use a different test library etc.