import subprocess

with open("pytest_utf8.log", "w", encoding="utf-8") as f:
    result = subprocess.run([".\\venv\\Scripts\\python.exe", "-m", "pytest", "tests/test_gateway.py", "--tb=short"], capture_output=True, text=True)
    f.write(result.stdout)
    f.write(result.stderr)
