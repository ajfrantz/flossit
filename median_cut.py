from PIL import Image
from pixel import Pixel
import os
import dmc_flosses

options = None

def largest_pop(blocks):
    def strategy(block):
        return len(block.points)
    return strategy
def side_length(blocks):
    def strategy(block):
        return block.longest_side_length()
    return strategy
def hybrid(blocks):
    num_by_pop = options.num_colors / 2
    if len(blocks) <= num_by_pop:
        return largest_pop(blocks)
    else:
        return side_length(blocks)
division_strategies = {
    'population' : largest_pop,
    'size'       : side_length,
    'hybrid'     : hybrid,
}

def average(l):
    return sum(l) / float(len(l))

def sum_squared_error(p1, p2):
    return sum([(x-y)**2 for x, y in zip(p1, p2)])

# A Block is a container for a number of points.  The class implements some
# logic to track the largest side of a such a collection of points, and
# facilitates breaking the collection into two equal-population subsections.
class Block:
    def __init__(self, points):
        # Make sure all of the points have the same number of elements
        assert all(len(points[0]) == len(p) for p in points)
        dimensionality = len(points[0])

        # Save the points, and then find the boundaries of this block.
        self.points = points
        self.mins = [min(vals) for vals in zip(*points)]
        self.maxes = [max(vals) for vals in zip(*points)]

    def longest_side_index(self):
        side_lengths = [high - low for low, high in zip(self.mins, self.maxes)]
        return side_lengths.index(max(side_lengths))

    def longest_side_length(self):
        idx = self.longest_side_index()
        return self.maxes[idx] - self.mins[idx]

    def split(self):
        idx = self.longest_side_index()
        self.points.sort(key = lambda point: point[idx])
        pivot = len(self.points) / 2
        return [Block(self.points[0:pivot]), Block(self.points[pivot:])]

    def color_error(self, rgb):
        return sum([sum_squared_error(rgb, point) for point in self.points])

    def __contains__(self, point):
        return all([low <= pt <= high for pt, low, high in zip(point, self.mins, self.maxes)])

    def __repr__(self):
        return '<Block() spanning %s to %s>' % (self.mins, self.maxes)

def get_image_points(image):
    x, y = image.size
    pixel_data = image.load()
    return [pixel_data[r,c] for r in range(x) for c in range(y)]

def subdivide(points):
    blocks = [Block(points)]
    while len(blocks) < options.num_colors:
        blocks.sort(key = division_strategies[options.strategy](blocks), reverse=True)
        longest_block = blocks[0]
        blocks = longest_block.split() + blocks[1:]
    return blocks

def find_nearest_floss(block):
    # This way searches full blown sum of squared error for best color
    #error = [block.color_error(floss['rgb']) for floss in dmc_flosses.flosses]
    # This way does a jenky averaged color search
    average_point = [average(coord) for coord in zip(*block.points)]
    error = [sum_squared_error(average_point, Pixel.FromRGB(floss['rgb']).get_Lab()) for floss in dmc_flosses.flosses]
    best_error = min(error)
    idx = error.index(best_error)
    return dmc_flosses.flosses[idx]

def map_blocks_to_floss(color_blocks):
    color_map = {}
    for block in color_blocks:
        color_map[block] = find_nearest_floss(block)
    return color_map

def floss_image(image, color_map):
    x, y = image.size
    pixel_data = image.load()
    flossed_image = Image.new('RGB', (x, y), None)
    flossed_pixels = flossed_image.load()
    for r in range(x):
        for c in range(y):
            value = Pixel.FromRGB(pixel_data[r,c]).get_Lab()
            possible_flosses = [floss for block, floss in color_map.iteritems() if value in block]
            # FIXME: I may be doing something weird because I seem to have pixels that can fall into multiple blocks
            #assert len(possible_flosses) == 1
            flossed_pixels[r,c] = possible_flosses[0]['rgb']
    
    # save debug image
    flossed_image.save(os.path.join(options.output_dir, 'floss.bmp'), 'BMP')
    return flossed_image

def flossit(resized_image, median_cut_options):
    global options
    options = median_cut_options
    assert options.num_colors > 0

    if not options.strategy:
        options.strategy = 'size'
    elif options.strategy not in division_strategies.keys():
        print '[Median Cut] Unknown division strategy "%s" -- falling back to size-based cuts!' % options.strategy
        options.strategy = 'size'

    print '[Median Cut] Enumerating the pixel data in the resized image...'
    all_points = [Pixel.FromRGB(rgb).get_Lab() for rgb in get_image_points(resized_image)]
    print '[Median Cut] Breaking image into %s discrete color groups...' % options.num_colors
    color_blocks = subdivide(all_points)
    print '[Median Cut] Finding best matching floss colors for each region...'
    color_map = map_blocks_to_floss(color_blocks)
    print '[Median Cut] Rendering image using appropriate floss colors...'
    return floss_image(resized_image, color_map)

