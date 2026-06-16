import os

routes_dir = r"c:\Users\egapn\Downloads\TugasBesarApsi\akhlak360\app\routes"
files = ["auth.py", "employee.py", "evaluator.py", "hr.py", "management.py"]

for filename in files:
    filepath = os.path.join(routes_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changed_count = 0
    new_lines = []
    for i, line in enumerate(lines):
        if '?' in line:
            # check if it looks like a sql query or the join function
            if 'SELECT' in line.upper() or 'INSERT' in line.upper() or 'UPDATE' in line.upper() or 'DELETE' in line.upper() or 'WHERE' in line.upper() or 'join' in line:
                changed_count += line.count('?')
                line = line.replace('?', '%s')
            else:
                # If there are ? in other places, we replace them too, but print a warning
                print(f"Warning: replacing ? in non-SQL line in {filename}:{i+1}: {line.strip()}")
                changed_count += line.count('?')
                line = line.replace('?', '%s')
        new_lines.append(line)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"{filename}: diganti {changed_count} placeholder.")
