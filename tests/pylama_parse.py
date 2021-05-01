"""Run Pylama and parse output to find errors and exit process with proper return code"""
import sys
import subprocess

output = subprocess.run('python -m pylama -o pylama.ini', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd='.',
                        shell=True)
errors = [line.decode('utf-8') for line in output.stdout.splitlines() if '[E]' in str(line)]
if errors:
    print(f'Found {len(errors)} errors:')
    for err in errors:
        print(str(err))

sys.exit(len(errors))
