# To install just on a per-project basis
# 1. Activate your virtual environemnt
# 2. uv add --dev rust-just
# 3. Use just within the activated environment

drive_uuid := "77688511-78c5-4de3-9108-b631ff823ef4"
user :=  file_stem(home_dir())
def_drive := join("/media", user, drive_uuid)
project := file_stem(justfile_dir())
local_env := join(justfile_dir(), ".env")


# list all recipes
default:
    just --list

# Install tools globally
tools:
    uv tool install twine
    uv tool install ruff

# Add conveniente development dependencies
dev:
    uv add --dev pytest

# Build the package
build:
    rm -fr dist/*
    uv build

# Publish the package to PyPi
publish pkg="zptess": build
    twine upload -r pypi dist/*
    uv run --no-project --with {{pkg}} --refresh-package {{pkg}} \
        -- python -c "from {{pkg}} import __version__; print(__version__)"

# Publish to Test PyPi server
test-publish pkg="zptess": build
    twine upload --verbose -r testpypi dist/*
    uv run --no-project  --with {{pkg}} --refresh-package {{pkg}} \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        -- python -c "from {{pkg}} import __version__; print(__version__)"

# Adds lica source library as dependency. 'version' may be a tag or branch
lica-dev version="main":
    #!/usr/bin/env bash
    set -exuo pipefail
    echo "Removing previous LICA dependency"
    uv add aiohttp pyserial-asyncio aioserial tabulate
    uv remove lica || echo "Ignoring non existing LICA library";
    if [[ "{{ version }}" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
        echo "Adding LICA source library --tag {{ version }}"; 
        uv add git+https://github.com/guaix-ucm/lica --tag {{ version }};
    else
        echo "Adding LICA source library --branch {{ version }}";
        uv add git+https://github.com/guaix-ucm/lica --branch {{ version }};
    fi

# Adds lica release library as dependency with a given version
lica-rel version:
    #!/usr/bin/env bash
    set -exuo pipefail
    echo "Removing previous LICA dependency"
    uv remove lica
    echo "Adding release version of LICA library";
    uv add --refresh-package lica lica[photometer,tabular];
    uv remove aiohttp aioserial pyserial-asyncio tabulate

# Backup .env to storage unit
env-bak drive=def_drive: (check_mnt drive) (env-backup join(drive, "env", project))

# Restore .env from storage unit
env-rst drive=def_drive: (check_mnt drive) (env-restore join(drive, "env", project))


# Starts a new database export migration cycle   
anew verbose="":
    #!/usr/bin/env bash
    set -exuo pipefail
    uv sync --reinstall
    uv run nx-db-schema --console --log-file nixnox.log {{ verbose }}
    uv run nx-db-populate --console --verbose  --trace --log-file nixnox.log {{ verbose }} all


# ========================= #
# QUCK COMMAND LINE TESTING #
# ========================= #

load:
    #!/usr/bin/env bash   
    set -exuo pipefail
    uv run nx-obs-load --console --verbose --trace observation --input-file TASD4B_AS_2024-10-23_224926_CASLEO.ecsv --text TASD4B_AS_2024-10-23_224926_CASLEO.txt
    uv run nx-obs-load --console --verbose --trace observation --input-file TASF46_AS_2024_10_05_042321_Yela.ecsv --text TASF46_AS_2024_10_05_042321_Yela.txt

import:
    #!/usr/bin/env bash   
    set -exuo pipefail
    uv run nx-db-import --console --verbose --trace all --folder export

export:
    #!/usr/bin/env bash   
    set -exuo pipefail
    uv run nx-db-export --console --verbose --trace all --folder export

# ============================== #
# NIXNOX WEB TEST AND PROTOTYPES #
# ============================== #

web:
    #!/usr/bin/env bash   
    set -exuo pipefail
    uv run streamlit run web_app.py

# =======================================================================

    

[private]
check_mnt mnt:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ ! -d  {{ mnt }} ]]; then
        echo "Drive not mounted: {{ mnt }}"
        exit 1 
    fi

[private]
env-backup bak_dir:
    #!/usr/bin/env bash
    set -exuo pipefail
    if [[ ! -f  {{ local_env }} ]]; then
        echo "Can't backup: {{ local_env }} doesn't exists"
        exit 1 
    fi
    mkdir -p {{ bak_dir }}
    cp {{ local_env }} {{ bak_dir }}
    cp nixnox.db {{ bak_dir }}
    cp *.ecsv {{ bak_dir }}
    cp *.txt {{ bak_dir }}
    cp -r .streamlit {{ bak_dir }}
  
[private]
env-restore bak_dir:
    #!/usr/bin/env bash
    set -euxo pipefail
    if [[ ! -f  {{ bak_dir }}/.env ]]; then
        echo "Can't restore: {{ bak_dir }}/.env doesn't exists"
        exit 1 
    fi
    cp {{ bak_dir }}/.env {{ local_env }}
    cp {{ bak_dir }}/nixnox.db .
    cp {{ bak_dir }}/*.ecsv .
    cp {{ bak_dir }}/*.txt .
    cp -r {{ bak_dir }}/.streamlit .
