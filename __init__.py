import network
import machine
import ujson
import io
import utime
import sys

NETCONFIG_FILE = '/netconfig.json'
GLOBAL_MACHINE_ID = ''.join(['{:02x}'.format(x) for x in machine.unique_id()])
DEFAULT_PASSWORD = 'micropythoN'
success = False
config = None
sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)

def read_yn(prompt):
  print(prompt + '? [y/N] -> ', end='')
  return sys.stdin.readline().strip().upper() == 'Y'

def setup():
  global config
  config = {}
  print('SSID -> ', end='')
  config['ssid'] = sys.stdin.readline().strip()
  print('Password -> ', end='')
  config['password'] = sys.stdin.readline().strip()
  print('Connect timeout (in seconds) -> ', end='')
  config['wait'] = int(sys.stdin.readline().strip())
  config['verbose'] = read_yn('Verbose')
  print(' -- config --')
  print(config)
  if read_yn('Save'):
    with open(NETCONFIG_FILE, 'wb') as f:
      f.write(ujson.dumps(config))
    print('Done!')
    if read_yn('Run'):
      run()

def print_status():
  global sta_if
  print("STA Active:", sta_if.active())
  print("STA Connected:", sta_if.isconnected())
  if (sta_if.isconnected()):
    print("STA ifconfig:", sta_if.ifconfig())
  print("AP Active:", ap_if.active())
  print("AP Connected:", ap_if.isconnected())
  print("AP ifconfig:", ap_if.ifconfig())

def is_connected():
  return sta_if.isconnected()

def run(wdt = None):
  global config
  global success
  global sta_if
  global ap_if
  have_file = False
  success = False
  try:
    with open(NETCONFIG_FILE, 'rb') as data_file:
      config = ujson.loads(data_file.read())
    have_file = True
    ap_if.active(False)
    sta_if.active(True)
    sta_if.connect(config['ssid'], config['password'])
    for i in range(config['wait']):
      if wdt is not None:
        wdt.feed()
      if config['verbose']:
        print('.', end='')
      if sta_if.isconnected():

        success = True
        break
      utime.sleep(1)
  except Exception as e:
    print("Exception:", e)
  if config['verbose']:
      print("")
  try:
    if not success:
      sta_if.active(False)
      ap_if.active(True)
      ap_if.config(essid="gx13-device-" + GLOBAL_MACHINE_ID, authmode=network.AUTH_WPA_WPA2_PSK, password=DEFAULT_PASSWORD)
      
      if not have_file: 
        while True:
          if wdt is not None:
            wdt.feed()
          print("Netconfig does not exist. Please run\nimport netconfig\nnetconfig.setup()\nCtrl-C to stop this output.")
          utime.sleep(1)
    else:
      ap_if.active(False)

    if config['verbose']:
      print_status()
  except Exception as e:
    print("Exception:", e)
    


def ensure_ok():
  if is_connected():
    return True
  run()
  return success