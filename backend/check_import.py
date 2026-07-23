import traceback
try:
    import tests.test_gateway
    print("Success")
except Exception as e:
    print(f"ERROR: {type(e).__name__} - {str(e)}")
    traceback.print_exc()
