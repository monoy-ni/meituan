from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import activity_agent.config as config
from activity_agent.config import AgentSettings, load_dotenv_file


class DotenvLoadingTests(unittest.TestCase):
    ENV_KEYS = [
        "ACTIVITY_AGENT_ENV_FILE",
        "ACTIVITY_AGENT_LLM_BASE_URL",
        "ACTIVITY_AGENT_LLM_API_KEY",
        "ACTIVITY_AGENT_STORAGE_PATH",
        "ACTIVITY_AGENT_DATA_MODE",
        "ACTIVITY_AGENT_MAP_PROVIDER",
        "AMAP_CITY",
    ]

    def setUp(self) -> None:
        self.original_env = {key: os.environ.get(key) for key in self.ENV_KEYS}
        for key in self.ENV_KEYS:
            os.environ.pop(key, None)
        self.original_cwd = os.getcwd()
        self.original_dotenv_loaded = config._DOTENV_LOADED
        config._DOTENV_LOADED = False

    def tearDown(self) -> None:
        os.chdir(self.original_cwd)
        for key in self.ENV_KEYS:
            os.environ.pop(key, None)
            if self.original_env[key] is not None:
                os.environ[key] = self.original_env[key]
        config._DOTENV_LOADED = self.original_dotenv_loaded

    def test_load_dotenv_file_preserves_existing_environment_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "ACTIVITY_AGENT_LLM_BASE_URL=https://dotenv.example/v1\n"
                "ACTIVITY_AGENT_LLM_API_KEY=dotenv-key\n",
                encoding="utf-8",
            )
            os.environ["ACTIVITY_AGENT_LLM_BASE_URL"] = "https://existing.example/v1"

            loaded = load_dotenv_file(env_path)

            self.assertTrue(loaded)
            self.assertEqual(os.environ["ACTIVITY_AGENT_LLM_BASE_URL"], "https://existing.example/v1")
            self.assertEqual(os.environ["ACTIVITY_AGENT_LLM_API_KEY"], "dotenv-key")

    def test_agent_settings_loads_dotenv_from_current_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "ACTIVITY_AGENT_LLM_BASE_URL=https://dotenv.example/v1\n"
                "ACTIVITY_AGENT_LLM_API_KEY=dotenv-key\n"
                "ACTIVITY_AGENT_STORAGE_PATH=./dotenv.sqlite3\n"
                "ACTIVITY_AGENT_DATA_MODE=hybrid\n"
                "ACTIVITY_AGENT_MAP_PROVIDER=amap\n"
                "AMAP_CITY=330100\n",
                encoding="utf-8",
            )
            os.chdir(tmp_dir)

            try:
                settings = AgentSettings.from_env()
            finally:
                os.chdir(self.original_cwd)

            self.assertEqual(settings.llm.base_url, "https://dotenv.example/v1")
            self.assertEqual(settings.llm.api_key, "dotenv-key")
            self.assertEqual(settings.storage.path, "./dotenv.sqlite3")
            self.assertEqual(settings.tools.data_mode, "hybrid")
            self.assertEqual(settings.tools.map_provider, "amap")
            self.assertEqual(settings.tools.amap_city, "330100")


if __name__ == "__main__":
    unittest.main()
