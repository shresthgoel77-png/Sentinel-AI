import traceback
try:
    import tests.test_gateway
except Exception as e:
    with open("err.txt", "w") as f:
        f.write(traceback.format_exc())
