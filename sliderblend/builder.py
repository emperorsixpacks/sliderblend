import os
import json
from pptx import Presentation

def load_template(template_name, templates_dir="templates"):
    """
    Loads a PowerPoint template by name from the provided templates directory.
    Looks up the template in the 'templates.json' file, retrieves its location,
    and initializes a Presentation object.
    
    Args:
        template_name (str): The key name of the template as defined in templates.json.
        templates_dir (str): Directory where the template files and templates.json are located.
    
    Returns:
        Presentation: A pptx Presentation object initialized with the specified template.
    
    Raises:
        ValueError: If the template name is not found in the JSON file.
    """
    # Path to the JSON file containing templates data
    json_path = os.path.join(templates_dir, "templates.json")
    with open(json_path, "r", "utf-8") as f:
        templates = json.load(f)
    
    if template_name not in templates:
        raise ValueError(f"Template '{template_name}' not found in {json_path}.")
    
    # Retrieve the absolute path to the template from the JSON data
    template_location = templates[template_name]["location"]
    
    # Initialize and return a Presentation object using the template location
    return Presentation(template_location)

# Example Usage:
if __name__ == "__main__":
    # Replace 'MyTemplate' with the actual key (template name) from your templates.json
    template_name = "MyTemplate"
    try:
        prs = load_template(template_name)
        print(f"Loaded template '{template_name}' successfully!")
    except ValueError as e:
        print(e)

