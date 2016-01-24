from PIL import Image
import os, sys, math, argparse
import dmc_flosses

# Parse command line options
parser = argparse.ArgumentParser(description = 'Tool to generate cross-stitch patterns from images')
parser.add_argument('input')
parser.add_argument('-o', '--output_dir', default='.')
parser.add_argument('-n', '--num_colors', type=int, default=16)
parser.add_argument('-a', '--algorithm', default='median_cut')
parser.add_argument('-s', '--strategy')
parser.add_argument('-k', '--kd_tree', action='store_true')
options = parser.parse_args()

def resize_image(filename):
    image = Image.open(filename)
    
    # resize the image so that it's at most 100 pixels on a side
    # while respecting aspect ratio
    (x,y) = image.size
    if x >= y:
        nx = 100
        ny = int(float(y)/float(x) * 100)
    else:
        ny = 100
        nx = int(float(x)/float(y) * 100)
    print 'Original image size (%d,%d)' % (x,y)
    print 'Resize image size (%d,%d)' % (nx,ny)
    print 'Final image size (%d,%d)' % (nx*4,ny*4)
    
    image = image.resize((nx,ny),Image.ANTIALIAS)
  
    # save debug image
    image.save(os.path.join(options.output_dir, 'resized.bmp'), 'BMP')
  
    return image

def patternify_image(flossed_image):
    nx, ny = flossed_image.size
    flossed_pixels = flossed_image.load()
    full_image = Image.new('RGB',(nx*4,ny*4),None)
    full_pixels = full_image.load()
    for j in range(nx):
        for k in range(ny):
            value = flossed_pixels[j,k]
            for l in range(4):
                for m in range(4):
                    if ((j==nx-1 and l==3 and m==3) or (k==ny-1 and l==3 and m==3)) and not (j==nx-1 and k==ny-1):
                        full_pixels[j*4+l,k*4+m] = (0,0,0)
                    elif (l == 3 or m == 3) and not (j == nx-1 and l==3) and not (k == ny-1 and m==3):
                        full_pixels[j*4+l,k*4+m] = (0,0,0)
                    else:
                        full_pixels[j*4+l,k*4+m] = value
    
    full_image.save(os.path.join(options.output_dir, 'full_floss.bmp'), 'BMP')
      

if __name__ == "__main__":
    try:
        algorithm = __import__(options.algorithm)
    except Exception as e:
        print 'Error with algorithm:', e
        sys.exit(1)

    print 'Resizing image into a reasonable stitching size...'
    resized = resize_image(options.input)

    print 'Flossing image using the "%s" algorithm...' % options.algorithm
    flossed = algorithm.flossit(resized, options)

    print 'Drawing pretty pattern-style version of image...'
    patternify_image(flossed)

