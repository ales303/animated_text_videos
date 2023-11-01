import os
import re
import subprocess

# Set the path to your project's root directory
project_path = './'


def find_python_files(path):
    """Return a list of paths to all .py files in the given directory and subdirectories."""
    python_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    print(f"Found {len(python_files)} Python files.")
    return python_files


def extract_imports(file_path):
    """Extract imported libraries from a .py file."""
    imports = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            match = re.match(r'^import (\w+)', line) or re.match(r'^from (\w+)', line)
            if match:
                imports.add(match.group(1))
    print(f"Extracted {len(imports)} imports from {file_path}.")
    return imports


def get_version(library):
    """Return the installed version of a library."""
    try:
        version = subprocess.check_output(["pip", "show", library]).decode('utf-8')
        match = re.search(r'^Version: (.+)$', version, re.MULTILINE)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"Error getting version for {library}: {e}")
        return None


def main():
    print("Starting process to generate requirements.txt ...")

    python_files = find_python_files(project_path)

    all_imports = set()
    for file in python_files:
        imports = extract_imports(file)
        all_imports.update(imports)

    print(f"Total unique imports found: {len(all_imports)}")

    requirements = []
    for lib in all_imports:
        version = get_version(lib)
        if version:
            requirements.append(f"{lib}=={version}")

    print(f"Writing {len(requirements)} library versions to requirements.txt ...")
    with open("requirements.txt", "w") as f:
        for req in requirements:
            f.write(req + '\n')

    print("requirements.txt generated successfully!")


if __name__ == "__main__":
    main()
