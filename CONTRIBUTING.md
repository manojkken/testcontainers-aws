# Contributing to testcontainers-aws

Thanks for your interest in contributing! Bug reports, feature ideas, docs fixes, and new service helpers are all welcome.

## Getting started

Requirements: Python 3.10+ and Docker (running).

```bash
git clone https://github.com/manojkken/testcontainers-aws.git
cd testcontainers-aws
python -m venv venv
source venv/bin/activate
pip install -e . -r requirements-dev.txt
```

## Running checks

```bash
pytest tests/ -v   # integration tests, spins up LocalStack
ruff check .       # lint
```

CI runs both on every pull request.

## Making a change

1. Open an issue first for anything non-trivial, so we can agree on the approach.
2. Create a branch from `main`.
3. Add or update tests in `tests/` for any behaviour change.
4. Update `README.md` and `CHANGELOG.md` if the change is user-facing.
5. Open a pull request describing what changed and why.

## Adding a new AWS service helper

Service managers live in `testcontainers_aws/services/`. Follow the pattern of an existing one (e.g. `sqs.py`):

- Wrap the boto3 client and expose small, well-named helper methods.
- Register the service in `AWSTestEnvironment` so `aws.<service>` works.
- Add integration tests that run against LocalStack.

Look for issues labelled [`good first issue`](https://github.com/manojkken/testcontainers-aws/labels/good%20first%20issue) if you want somewhere to start.
