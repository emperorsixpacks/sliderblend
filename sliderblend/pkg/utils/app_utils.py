import os


def return_base_dir():
    return os.path.dirname(os.path.dirname(__file__))


def exists(path: str) -> bool:
    return os.path.exists(path)


class Prompt:
    def __init__(self, prompt_name: str, /, **kwargs: str) -> None:
        self.prompt_name = prompt_name
        self.prompt_path = os.path.join(BASE_DIR, f"prompts/{self.prompt_name}.txt")
        self.prompt_params = kwargs

    def read(self) -> str:
        prompt: str = None
        if not exists(self.prompt_path):
            raise FileNotFoundError(f"Prompt {self.prompt_name} does not exist")
        with open(self.prompt_path, encoding="utf-8") as file:
            prompt = file.read()
            file.close()

        return prompt.format_map(self.prompt_params)
