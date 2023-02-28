import os
import threading

r, w = os.pipe()
# r, w = os.fdopen(r, 'rb'), os.fdopen(w, 'wb')

def a():
    print("start")
    while True:
        print(os.read(r, 10))

threading.Thread(target=a, daemon=True).start()

while True:
    # print('>')
    os.write(w, input().encode())
