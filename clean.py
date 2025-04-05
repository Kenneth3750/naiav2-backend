# Read requirements.txt
with open('requirements.txt', 'r') as f:
    requirements = f.readlines()

# Process requirements
cleaned_requirements = []
for line in requirements:
    if '@' not in line:
        cleaned_requirements.append(line)
    else:
        # Extract just the package name
        package_name = line.split('@')[0].strip()
        cleaned_requirements.append(f"{package_name}\n")

# Write back to the same file
with open('requirements.txt', 'w') as f:
    f.writelines(cleaned_requirements)