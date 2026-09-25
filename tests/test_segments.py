"""Tests for vermink.segments module."""

from vermink.segments import abbreviate, value


class TestAbbreviate:
    def test_home_root(self):
        assert abbreviate("/home/user", "/home/user") == "~"

    def test_subdirectory(self):
        assert abbreviate("/home/user", "/home/user/projects/demo") == "~/projects/demo"

    def test_unrelated_path(self):
        assert abbreviate("/home/user", "/tmp/work") == "/tmp/work"

    def test_root_home(self):
        assert abbreviate("/", "/") == "~"

    def test_trailing_slash(self):
        assert abbreviate("/home/user/", "/home/user/projects") == "~/projects"


class TestValue:
    def test_user_from_env(self):
        assert value("user", env={"USER": "alice"}) == "alice"

    def test_user_from_username(self):
        assert value("user", env={"USERNAME": "bob"}) == "bob"

    def test_user_empty(self):
        assert value("user", env={}) == ""

    def test_host_from_hostname(self):
        assert value("host", env={"HOSTNAME": "myhost"}) == "myhost"

    def test_host_from_computername(self):
        assert value("host", env={"COMPUTERNAME": "win-pc"}) == "win-pc"

    def test_dir_abbreviated(self):
        result = value("dir", env={"HOME": "/home/user"}, cwd="/home/user/projects")
        assert result == "~/projects"

    def test_dir_not_in_home(self):
        result = value("dir", env={"HOME": "/home/user"}, cwd="/tmp/work")
        assert result == "/tmp/work"

    def test_git_branch(self, tmp_path):
        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        # 显式建分支，不依赖 git init.defaultBranch 的本地默认值
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp_path, check=True, capture_output=True,
        )
        result = value("git", cwd=str(tmp_path))
        assert result == "main"

    def test_git_not_repo(self, tmp_path):
        assert value("git", cwd=str(tmp_path)) == ""

    def test_time_format(self):
        result = value("time")
        assert len(result) == 5
        assert ":" in result

    def test_exit_code_nonzero(self):
        result = value("exit_code", env={"J_EXIT_CODE": "1"})
        assert result == "x1"

    def test_exit_code_zero(self):
        result = value("exit_code", env={"J_EXIT_CODE": "0"})
        assert result == ""

    def test_exit_code_missing(self):
        result = value("exit_code", env={})
        assert result == ""

    def test_venv(self):
        result = value("venv", env={"VIRTUAL_ENV": "/home/user/.venvs/myenv"})
        assert result == "myenv"

    def test_conda(self):
        result = value("venv", env={"CONDA_PREFIX": "/opt/conda/envs/ml"})
        assert result == "ml"

    def test_no_venv(self):
        result = value("venv", env={})
        assert result == ""

    def test_unknown_segment(self):
        assert value("not_real", env={}) == ""
