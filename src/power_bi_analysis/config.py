"""
Configuration management for Insight Fabric.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG_DIR = Path.home() / ".insight-fabric"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


class Config:
    """Configuration manager for Insight Fabric."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to config file (default: ~/.insight-fabric/config.json)
        """
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.data: Dict[str, Any] = self._load_defaults()
        self.load()

    def _load_defaults(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "llm": {
                "provider": "openai",
                "api_key": None,
                "model": None,
                "options": {},
                "providers": {
                    "openai": {
                        "api_key": None,
                        "model": "gpt-4-turbo-preview",
                        "base_url": None,
                    },
                    "anthropic": {
                        "api_key": None,
                        "model": "claude-3-5-sonnet-20241022",
                    },
                    "gemini": {
                        "api_key": None,
                        "model": "gemini-2.0-flash-exp",
                    },
                    "deepseek": {
                        "api_key": None,
                        "model": "deepseek-chat",
                        "base_url": "https://api.deepseek.com",
                    }
                }
            },
            "output": {
                "default_dir": str(Path.cwd() / "analysis_output"),
                "generate_yaml": True,
            },
            "extraction": {
                "max_file_size_mb": 100,
                "timeout_seconds": 30,
            }
        }

    def load(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._merge_dicts(self.data, loaded)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save config file {self.config_file}: {e}")

    def _merge_dicts(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Recursively merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dicts(target[key], value)
            else:
                target[key] = value

    def get_llm_provider(self) -> str:
        """Get configured LLM provider."""
        return self.data["llm"]["provider"]

    def set_llm_provider(self, provider: str) -> None:
        """Set LLM provider."""
        self.data["llm"]["provider"] = provider

    def get_llm_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """Get API key for provider (or current provider)."""
        provider = provider or self.get_llm_provider()
        # First check provider-specific config
        provider_config = self.data["llm"]["providers"].get(provider, {})
        api_key = provider_config.get("api_key")
        if api_key:
            return api_key
        # Fallback to global api_key
        return self.data["llm"].get("api_key")

    def set_llm_api_key(self, api_key: str, provider: Optional[str] = None) -> None:
        """Set API key for provider (or current provider)."""
        provider = provider or self.get_llm_provider()
        if provider not in self.data["llm"]["providers"]:
            self.data["llm"]["providers"][provider] = {}
        self.data["llm"]["providers"][provider]["api_key"] = api_key
        # Also set global api_key for backward compatibility
        self.data["llm"]["api_key"] = api_key

    def get_llm_model(self, provider: Optional[str] = None) -> Optional[str]:
        """Get model for provider (or current provider)."""
        provider = provider or self.get_llm_provider()
        provider_config = self.data["llm"]["providers"].get(provider, {})
        model = provider_config.get("model")
        if model:
            return model
        return self.data["llm"].get("model")

    def set_llm_model(self, model: str, provider: Optional[str] = None) -> None:
        """Set model for provider (or current provider)."""
        provider = provider or self.get_llm_provider()
        if provider not in self.data["llm"]["providers"]:
            self.data["llm"]["providers"][provider] = {}
        self.data["llm"]["providers"][provider]["model"] = model
        # Also set global model for backward compatibility
        self.data["llm"]["model"] = model

    def get_llm_options(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get provider-specific options."""
        provider = provider or self.get_llm_provider()
        provider_config = self.data["llm"]["providers"].get(provider, {})
        options = provider_config.get("options", {})
        # Include base_url if present
        if "base_url" in provider_config:
            options["base_url"] = provider_config["base_url"]
        return options

    def set_llm_option(self, key: str, value: Any, provider: Optional[str] = None) -> None:
        """Set a provider-specific option."""
        provider = provider or self.get_llm_provider()
        if provider not in self.data["llm"]["providers"]:
            self.data["llm"]["providers"][provider] = {}
        if "options" not in self.data["llm"]["providers"][provider]:
            self.data["llm"]["providers"][provider]["options"] = {}
        self.data["llm"]["providers"][provider]["options"][key] = value

    def get_output_dir(self) -> Path:
        """Get default output directory."""
        dir_str = self.data["output"].get("default_dir")
        return Path(dir_str) if dir_str else Path.cwd() / "analysis_output"

    def set_output_dir(self, directory: Path) -> None:
        """Set default output directory."""
        self.data["output"]["default_dir"] = str(directory)

    def get_generate_yaml(self) -> bool:
        """Get whether to generate YAML by default."""
        return self.data["output"].get("generate_yaml", True)

    def set_generate_yaml(self, generate: bool) -> None:
        """Set whether to generate YAML by default."""
        self.data["output"]["generate_yaml"] = generate


def configure_interactive():
    """Interactive configuration wizard."""
    config = Config()

    print("=== Insight Fabric Configuration ===\n")

    # LLM Provider
    providers = ["openai", "anthropic", "gemini", "deepseek"]
    print("Available LLM providers:")
    for i, provider in enumerate(providers, 1):
        print(f"  {i}. {provider}")
    choice = input(f"\nSelect provider (1-{len(providers)}) [default: {config.get_llm_provider()}]: ").strip()
    if choice:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(providers):
                config.set_llm_provider(providers[idx])
        except ValueError:
            pass

    provider = config.get_llm_provider()

    # API Key
    current_key = config.get_llm_api_key(provider)
    key_prompt = f"Enter {provider} API key"
    if current_key:
        key_prompt += f" (leave blank to keep current: {current_key[:4]}...)"
    key = input(f"{key_prompt}: ").strip()
    if key:
        config.set_llm_api_key(key, provider)

    # Model
    current_model = config.get_llm_model(provider)
    model_prompt = f"Enter model name for {provider}"
    if current_model:
        model_prompt += f" (default: {current_model})"
    model = input(f"{model_prompt}: ").strip()
    if model:
        config.set_llm_model(model, provider)

    # Base URL (for OpenAI-compatible providers)
    if provider in ["openai", "deepseek"]:
        options = config.get_llm_options(provider)
        current_base_url = options.get("base_url")
        base_url_prompt = "Enter base URL (for OpenAI-compatible providers like DeepSeek)"
        if current_base_url:
            base_url_prompt += f" (default: {current_base_url})"
        base_url = input(f"{base_url_prompt}: ").strip()
        if base_url:
            config.set_llm_option("base_url", base_url, provider)

    # Output directory
    current_dir = config.get_output_dir()
    dir_prompt = f"Enter default output directory (default: {current_dir}): "
    new_dir = input(dir_prompt).strip()
    if new_dir:
        config.set_output_dir(Path(new_dir))

    # Generate YAML by default
    current_yaml = config.get_generate_yaml()
    yaml_choice = input(f"Generate YAML by default? (y/n) [default: {'y' if current_yaml else 'n'}]: ").strip().lower()
    if yaml_choice:
        config.set_generate_yaml(yaml_choice.startswith('y'))

    # Save
    config.save()
    print(f"\nConfiguration saved to {config.config_file}")
    print("You can now use the tool without providing API keys each time.")


if __name__ == "__main__":
    configure_interactive()