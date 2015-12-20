import ssl, json, zmq, os, logging, sys, sched, time, signal 
from urllib.request import Request, urlopen 
from datetime import datetime, timedelta

def signal_handler(signal, frame):
  print('You pressed Ctrl+C! Shutting down')
  socket.close(linger=1)
  sys.exit(0)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.DEBUG)
report_time = float(os.getenv('ELECTRIC_REPORT_TIME', 3600))
socket_address = os.getenv('ELECTRIC_SOCKET')
api_url = os.getenv('ELECTRIC_API_URL')
api_token = os.getenv('ELECTRIC_API_TOKEN')

context = zmq.Context()
socket = context.socket(zmq.PUSH)
logging.info('Connected to address %s',socket_address)
socket.connect(socket_address)

def send(message):
  logging.debug('Send value: %s to server',message)
  socket.send_json(message)

def convert_time(unix_time):
    return datetime.fromtimestamp(unix_time).strftime('%Y-%m-%dT%H:%M:%SZ')

def get_data_from_api():
  q = Request(api_url)
  q.add_header('Accept', 'application/json')
  q.add_header('X-Version', '1.0')
  q.add_header('X-Token', api_token)
  response = urlopen(q, context=ssl._create_unverified_context()).read()
  return json.loads(response.decode('utf-8'))

def report(sc):
  filterd_elements = [element for element in get_data_from_api() if element[1] !='nan']
  messages = [{'name':'Electrical sensor',
      'type':'external_api', 
      'datetime':convert_time(element[0]), 
      'value':element[1]} for element in filterd_elements]
  [send(message) for message in messages]
  sc.enter(report_time, 1, report, (sc,))

s = sched.scheduler(time.time, time.sleep)
s.enter(report_time, 1, report, (s,))
logging.info('Add report jobb to scheduler, will run every %s second', report_time)
s.run()