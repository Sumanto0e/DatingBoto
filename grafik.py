import threading
import time


def my_timer(print_interval):
    for i in range(print_interval):
        time.sleep(1)
        print(i)

while True:
    com = input()
    if com == 'start timer':
        t = threading.Thread(target=my_timer, args=(int(input('Введи число: ')),))
        t.start()
    else:
        print('no command')