"""
A set of scripts to read the HD-LBP serial stream
"""
import serial
import threading
import decimal

def readCamera(device):
  cam = serial.Serial(device, 9600, timeout=1)
  keys = ['time', 'centroid_x', 'centroid_y', 'centroid_r', 
          'level_1', 'level_2', 'level_3',
          'width_1', 'width_2', 'width_3',
          'height_1', 'height_2', 'height_3',
          'power']
  buffer = ''
  while True:
    buffer = buffer + cam.read(cam.inWaiting())
    if buffer.count('\n') > 2:
      lines = buffer.split('\n') # Guaranteed to have at least 2 entries
      last_line = lines[-2]
      # buffer = lines[-1]
      header, values = last_line.split("R ",1)
      floats = [float(x) for x in values.split()]
      output = dict(zip(keys, floats))
      return output

def findBeam(controller, z):
  controller.groupVelocity(1, 30)
  controller.groupMoveLine(1, [-120, z])
  while controller.axis2.getMotionStatus():
    pass
  while controller.axis3.getMotionStatus():
    pass
  controller.groupVelocity(1, 5)
  controller.groupMoveLine(1, [120, z])
  start_position = [-120, z]
  while controller.axis2.getMotionStatus():
    if readCamera('/dev/ttyUSB1')['power'] > 0.002:
      start_position = map(int, controller.groupPosition(1))
      print 'Crossed beam!'
  controller.groupVelocity(1, 30)
  controller.groupMoveLine(1, start_position)
  while controller.axis2.getMotionStatus():
      pass
  fine_sampling = [[round(y, 4), z] for y in [decimal.Decimal(start_position[0] - 10 + x/10.) for x in range(0, 20 * 10)]]
  controller.groupVelocity(1, 10)
  for position in fine_sampling:
    controller.groupMoveLine(1, position)
    while controller.axis2.getMotionStatus():
      pass
    cam_reading = readCamera('/dev/ttyUSB1')
    if abs(cam_reading['centroid_x']) < 100 and cam_reading['power'] > 0.002:
      break
  return controller.groupPosition(1)