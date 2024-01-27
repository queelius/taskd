import os
import subprocess
import uuid

def execute_script(workspace_path, script_name):
    script_path = os.path.join(workspace_path, script_name)
    with open(os.path.join(workspace_path, f"{uuid.uuid4()}_output.log"), "w") as output_file:
        subprocess.run(["python", script_path], stdout=output_file, stderr=subprocess.STDOUT)

def format_docstring(docstring):
    if not docstring:
        return "No description available"

    # Split the docstring into lines
    lines = docstring.split('\n')

    # Remove leading/trailing whitespace and dedent each line
    cleaned_lines = [line.strip() for line in lines]

    # Join the lines back with newline characters
    return '\n'.join(cleaned_lines)