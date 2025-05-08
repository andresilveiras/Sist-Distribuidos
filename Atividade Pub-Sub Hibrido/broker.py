import zmq

context = zmq.Context()

frontend = context.socket(zmq.XSUB)
frontend.bind("tcp://*:5559")  # Recebe dos publishers

backend = context.socket(zmq.XPUB)
backend.bind("tcp://*:5560")   # Envia aos subscribers

print("Broker iniciado...")
zmq.proxy(frontend, backend)
