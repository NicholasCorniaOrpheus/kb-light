## Package installation

### Using [pip](https://pip.pypa.io/en/stable/getting-started/)

Generate the virtual environment on your project folder:

```bash
# Generate local python binaries in folder
python3 -m venv kb-light-env
```

Activate virtual environment in order to invoke the package:

```bash
# activate the environment for this terminal
source kb-light-env/bin/activate
```

```bash
pip install kblight
```

### Using [uv](https://docs.astral.sh/uv)

Generate the virtual environment on your project folder:

```bash
# Generate local python binaries in folder
uv venv
```

Activate virtual environment in order to invoke the package:

```bash
# activate the environment for this terminal
source .venv/bin/activate
```

```bash
uv add kblight
uv pip install kblight 
```

### Python for Windows and Mac users

Have a look at this detailed [documentation](https://realpython.com/installing-python/).
