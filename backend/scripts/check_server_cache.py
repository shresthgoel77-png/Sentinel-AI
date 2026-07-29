import requests
import time

BASE = 'http://127.0.0.1:8000'

def create_task():
    with open('../README.md','rb') as f:
        r = requests.post(f'{BASE}/api/scan', files={'file': f})
        r.raise_for_status()
        return r.json().get('task_id')

def get_status(task_id):
    r = requests.get(f'{BASE}/api/status/{task_id}')
    return r

if __name__ == '__main__':
    tid = create_task()
    print('created', tid)
    for i in range(6):
        r = get_status(tid)
        print(i, r.status_code, r.text[:200])
        time.sleep(1)
    print('Now wait 10s for TTL eviction (if TTL configured low)')
    time.sleep(10)
    r = get_status(tid)
    print('after wait:', r.status_code, r.text[:200])
