# Begin

## Init project environment

- git init
- git config
- poetry install
- git commit

## Develop

- code
- git commit
- tox

## Delivery

### Run tox

Run tox to format code style and check test.

```shell script
tox
```

### Git tag

Modify package version value, then commit.

Add tag

```shell script
git tag -a v0.1.0
```

### Build

Build this tag distribution package.

```shell script
poetry build
```

### Upload index server

Upload to pypi server, or pass `--repository https://pypi.org/simple` to specify index server.

```shell script
poetry publish
```

## Develop guide

### Pycharm Configuration

Open project use Pycharm.

#### Module can not import in src

Check menu bar, click `File` --> `Settings` --> `Project Settings` --> `Project Structure` .
Mark `src` and `tests` directory as sources.

#### Enable pytest

Click `File` --> `Settings` --> `Tools` --> `Python Integrated Tools` --> `Testing` --> `Default runner`, then select
`pytest`.

If you run test by `Unittests` before, you should delete configuration. Open `Edit Run/Debug configurations dialog` in
In the upper right corner of Pycharm window, then delete configuration.

### Others

You should confirm `src` directory in `sys.path`. You can add it by `sys.path.extend(['/tmp/demo/src'])` if it not exist.

## 参考

[Python 项目工程化开发指南](https://pyloong.github.io/)

## 项目结构

项目主要包含以下目录和文件：

```
/Users/costalong/code/ai/translate-demo/translate_demo/
├── .editorconfig
├── .github/
│   └── workflows/
│       └── main.yml
├── .gitignore
├── .pre-commit-config.yaml
├── .pytest_cache/
│   ├── .gitignore
│   ├── CACHEDIR.TAG
│   ├── README.md
│   └── v/
│       └── cache/
├── LICENSE
├── README.md
├── __init__.py
├── __pycache__/
│   ├── __init__.cpython-313.pyc
│   └── llm.cpython-313.pyc
├── docs/
│   └── development.md
├── poetry.lock
├── pyproject.toml
├── src/
│   ├── agents/
│   │   ├── TranslatorAgent.py
│   │   ├── __init__.py
│   │   └── __pycache__/
│   ├── llm_core/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── base.py
│   │   ├── config.py
│   │   ├── deepseek/
│   │   ├── factory.py
│   │   ├── ollama/
│   │   ├── openai/
│   │   └── providers.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   └── translate/
│   └── translate_demo/
│       ├── __init__.py
│       ├── __pycache__/
│       ├── cmd.py
│       ├── cmdline.py
│       ├── config/
│       └── log.py
├── test_import.py
├── tests/
│   ├── __init__.py
│   ├── __pycache__/
│   │   ├── __init__.cpython-313.pyc
│   │   ├── conftest.cpython-313-pytest-7.4.4.pyc
│   │   ├── conftest.cpython-313-pytest-8.3.5.pyc
│   │   ├── test_llm.cpython-313-pytest-7.4.4.pyc
│   │   └── test_llm.cpython-313-pytest-8.3.5.pyc
│   ├── conftest.py
│   ├── settings.yml
│   ├── test_llm.py
│   ├── test_llm_new.py
│   └── test_version.py
└── tox.ini
```

## 依赖管理

项目使用 `poetry` 进行依赖管理，`pyproject.toml` 文件中定义了项目的依赖和开发依赖。你可以使用以下命令来安装依赖：

```shell script
poetry install
```

如需添加新的依赖，可以使用以下命令：

```shell script
poetry add <package_name>
```

如需添加开发依赖，可以使用以下命令：

```shell script
poetry add --group dev <package_name>
```
