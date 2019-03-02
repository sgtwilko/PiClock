import os
import time
import threading
import Queue


class TTSThread(threading.Thread):
    def __init__(self, tts_q=Queue.Queue()):
        super(TTSThread, self).__init__()
        self.tts_q = tts_q
        self.stoprequest = threading.Event()

    def run(self):
        while not self.stoprequest.isSet():
            try:
                options = ""
                message = self.tts_q.get(True, 0.05)
                if isinstance(message, tuple):
                    message, options = message
                if isinstance(options, tuple):
                    options = ' '.join(options)
                print('mimic -t "'+message+'" '+options)
                os.system('mimic -t "'+message+'" '+options)
            except Queue.Empty:
                continue

    def join(self, timeout=None):
        self.stoprequest.set()
        super(TTSThread, self).join(timeout)

    def say(self, text):
        self.tts_q.put(text)


if __name__ == '__main__':
    ttsThread = TTSThread()
    ttsThread.start()

    ttsThread.say(("testing this queue thing", ("--setf int_f0_target_mean=165")))
    ttsThread.say("testing this queue thing")
    ttsThread.say("testing this queue thing")
    time.sleep(60)
    ttsThread.join()
