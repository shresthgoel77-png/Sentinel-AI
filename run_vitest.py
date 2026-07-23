import subprocess
with open("vitest_utf8.log", "w", encoding="utf-8") as f:
    result = subprocess.run("npx vitest run src/components/__tests__/GatewayDemo.test.tsx", shell=True, capture_output=True, text=True)
    f.write(result.stdout)
    f.write(result.stderr)
