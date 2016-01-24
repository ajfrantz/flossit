import math

class Pixel:
  def __init__(self):
    # initialize to black in both color spaces
    self.colors = {}
    self.colors['rgb'] = (0,0,0)
    self.colors['Lab'] = (0,0,0)

  def __set_Lab(self, Lab):
    self.colors.clear()
    self.colors['Lab'] = Lab

  def __set_RGB(self, rgb):
    self.colors.clear()
    self.colors['rgb'] = rgb

  def __RGB_to_Lab(self,rgb):
    r,g,b = rgb
    

    # Move RGB values into the range [0,1]
    r = float(r) / 255
    g = float(g) / 255
    b = float(b) / 255


    # Convert to CIEXYZ color space
    def normalize(v):
        if v > 0.04045:
            return 100 * math.pow((v + 0.055)/1.055,2.4)
        else:
            return 100 * v / 12.92
    r = normalize(r)
    g = normalize(g)
    b = normalize(b)

    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    #return (x,y,z)


    # Convert from CIEXYZ to CIELAB
    x = x / 95.047
    y = y / 100.0
    z = z / 108.883

    if x > 0.008856:
      x = math.pow(x,1.0/3.0)
    else:
      x = 7.787 * x + 16/116.0
    if y > 0.008856:
      y = math.pow(y,1.0/3.0)
    else:
      y = 7.787 * y + 16/116.0
    if z > 0.008856:
      z = math.pow(z,1.0/3.0)
    else:
      z = 7.787 * z + 16/116.0

    L = (116 * y) - 16
    a = 500 * (x-y)
    b = 200 * (y-z)
    

    return (L,a,b)

  def __Lab_to_RGB(self,Lab):
    L,a,b = Lab

    # Convert CIELAB to CIEXYZ
    y = (float(L) + 16) / 116.0
    x = float(a) / 500 + y
    z = y - float(b) / 200

    if math.pow(y,3) > 0.008856:
      y = math.pow(y,3)
    else:
      y = (y - 16) / 116.0
    if math.pow(x,3) > 0.008856:
      x = math.pow(x,3)
    else:
      x = (x - 16) / 116.0
    if math.pow(z,3) > 0.008856:
      z = math.pow(z,3)
    else:
      z = (z - 16) / 116.0

    x = 95.047 * x
    y = 100 * y
    z = 108.883 * z

    # Convert CIEXYZ to RGB
    x = x / 100
    y = y / 100
    z = z / 100

    r = x * 3.2406 + y * -1.5372 + z * -0.4986;
    g = x * -0.9689 + y * 1.8758 + z * 0.0415;
    b = x * 0.0557 + y * -0.2040 + z * 1.0570

    if r > 0.0031308:
      r = 1.055 * math.pow(r,1.0/2.4) - 0.055
    else:
      r = 12.92 * r
    if g > 0.0031308:
      g = 1.055 * math.pow(g,1.0/2.4) - 0.055
    else:
      g = 12.92 * g
    if b > 0.0031308:
      b = 1.055 * math.pow(b,1.0/2.4) - 0.055
    else:
      b = 12.92 * b

    r = math.floor(r + 0.5)
    g = math.floor(g + 0.5)
    b = math.floor(b + 0.5)

    return (r,g,b)

  def get_Lab(self):
    # if this transform isn't cached, calculate it
    if 'Lab' not in self.colors:
       self.colors['Lab'] = self.__RGB_to_Lab(self.colors['rgb'])
    return self.colors['Lab']

  def get_RGB(self):
    # if this transform isn't cached, calculate it
    if 'rgb' not in self.colors:
       self.colors['rgb'] = self.__Lab_to_RGB(self.colors['Lab'])
    return self.colors['rgb']
    
  @staticmethod
  def FromRGB(rgb):
    pixel = Pixel()
    pixel.__set_RGB(rgb)
    return pixel
  
  @staticmethod
  def FromLab(Lab):
    pixel = Pixel()
    pixel.__set_Lab(Lab)
    return pixel

