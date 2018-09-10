import sys
import cPickle as pickle

rawinput = sys.argv[1]
rawinput = rawinput.replace('\n', '').replace('\r', '')
input = rawinput.decode("base64")
data = pickle.loads(input)
print(data)
