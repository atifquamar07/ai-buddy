import json
import re

def fix_truncated_json(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Find the last complete object
    last_complete_object = content.rfind('  },\n  {')
    if last_complete_object == -1:
        raise ValueError("No complete object found")

    # Trim the content to the last complete object
    trimmed_content = content[:last_complete_object + 4]  # Include the closing brace

    # Add closing brackets for the main structure
    trimmed_content += '\n  ]\n}'

    # Remove any truncated strings at the end
    trimmed_content = re.sub(r'"[^"]*$', '', trimmed_content)

    # Validate the fixed JSON
    
    try:
        json.loads(trimmed_content)
    except json.JSONDecodeError as e:
        print(f"Error: The fixed JSON is still invalid. {e}")
        return

    # Write the fixed JSON to the output file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(trimmed_content)

    print(f"Fixed JSON has been written to {output_file}")

# Use the function
input_file = '/hci/finetuning/samantha-1.1.json'
output_file = '/hci/finetuning/samantha-1.1-fixed.json'
fix_truncated_json(input_file, output_file)