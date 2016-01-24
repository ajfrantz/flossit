from PIL import Image
from itertools import groupby, compress
from pixel import Pixel
import os, random
import dmc_flosses

options = None

def random_points_in_region(points, num_regions):
    mins  = [min(vals) for vals in zip(*points)]
    maxes = [max(vals) for vals in zip(*points)]
    return [[random.randrange(low, high, 1) for low, high in zip(mins, maxes)] for i in range(num_regions)]
seed_strategies = {
    'forgy'  : random.sample,
    'random' : random_points_in_region,
}

def average(l):
    return sum(l) / float(len(l))

def sum_squared_error(p1, p2):
    return sum([(x-y)**2 for x, y in zip(p1, p2)])

def get_image_points(image):
    x, y = image.size
    pixel_data = image.load()
    return [pixel_data[r,c] for r in range(x) for c in range(y)]

class Node: pass

def kdtree(point_list, depth = 0):
    if not point_list:
        return

    # Select axis based on depth so that axis cycles through all valid values
    k = len(point_list[0])
    axis = depth % k
 
    # Sort point list and choose median as pivot element
    point_list.sort(key=lambda point: point[axis])
    median = len(point_list) // 2 # choose median
 
    # Create node and construct subtrees
    node = Node()
    node.location = point_list[median]
    node.left_child = kdtree(point_list[:median], depth + 1)
    node.right_child = kdtree(point_list[median + 1:], depth + 1)
    return node

def nearest_neighbor(point, kd_tree, depth = 0):
    if not kd_tree:
        return None, None

    # Select axis based on depth so that axis cycles through all valid values
    k = len(kd_tree.location)
    axis = depth % k
    
    # Determine if this point is "left" or "right" of this axis split
    if point[axis] < kd_tree.location[axis]:
        explore_order = [kd_tree.left_child, kd_tree.right_child]
    else:
        explore_order = [kd_tree.right_child, kd_tree.left_child]

    # Explore the side this point is on.
    current_best, current_best_error = nearest_neighbor(point, explore_order[0], depth + 1)

    # Test to see if we ourselves are a better point.
    my_error = sum_squared_error(point, kd_tree.location)
    if not current_best or current_best_error > my_error:
        current_best = kd_tree.location
        current_best_error = my_error

    # Test if we need to check the other side too.
    if (kd_tree.location[axis] - current_best[axis])**2 >= current_best_error:
        # Need to test the other side as well.
        alternate, alternate_error = nearest_neighbor(point, explore_order[0], depth + 1)
        if alternate_error < current_best_error:
            current_best = alternate
            current_best_error = alternate_error

    # Finally we know we have the best point so far, so return it.
    return current_best, current_best_error

def closest_region(point, regions, kd_tree):
    global options
    if options.kd_tree:
        nn, nn_error = nearest_neighbor(point, kd_tree)
        return regions.index(nn)
    else:
        errors = [sum_squared_error(point, region_point) for region_point in regions]
        return errors.index(min(errors))
        

def central_point(points):
    return [average(dimension) for dimension in zip(*points)]

def find_nearest_floss(region_point):
    error = [sum_squared_error(region_point, Pixel.FromRGB(floss['rgb']).get_Lab()) for floss in dmc_flosses.flosses]
    best_error = min(error)
    idx = error.index(best_error)
    return dmc_flosses.flosses[idx]

def floss_image(image, region_points, region_colors):
    x, y = image.size
    pixel_data = image.load()
    flossed_image = Image.new('RGB', (x, y), None)
    flossed_pixels = flossed_image.load()
    for r in range(x):
        for c in range(y):
            pixel = Pixel.FromRGB(pixel_data[r,c]).get_Lab()
            error = [sum_squared_error(pixel, region_point) for region_point in region_points]
            best_error = min(error)
            idx = error.index(best_error)
            flossed_pixels[r,c] = region_colors[idx]['rgb']
    
    # save debug image
    flossed_image.save(os.path.join(options.output_dir, 'floss.bmp'), 'BMP')
    return flossed_image

def flossit(resized_image, median_cut_options):
    global options
    options = median_cut_options
    assert options.num_colors > 0

    if not options.strategy:
        options.strategy = 'random'
    elif options.strategy not in seed_strategies.keys():
        print '[Lloyd\'s] Unknown seeding strategy "%s" -- falling back to random seeds!' % options.strategy
        options.strategy = 'random'

    print '[Lloyd\'s] Enumerating the pixel data in the resized image...'
    all_points = [Pixel.FromRGB(rgb).get_Lab() for rgb in get_image_points(resized_image)]
    print '[Lloyd\'s] Setting initial seed regions...'
    regions = seed_strategies[options.strategy](all_points, options.num_colors)
    region_kd_tree = kdtree(regions)
    print '[Lloyd\'s] Finding initial point assignments...'
    assignments = [closest_region(point, regions, region_kd_tree) for point in all_points]
    iteration = 1
    last_assignments = []
    while last_assignments != assignments:
        print '[Lloyd\'s] Iterating regions (%s)...' % iteration

        populated_regions = [k for k, g in groupby(sorted(assignments))]
        regions = [central_point(compress(all_points, [assignment == region for assignment in assignments])) for region in populated_regions]
        region_kd_tree = kdtree(regions)

        iteration += 1
        last_assignments = assignments
        assignments = [closest_region(point, regions, region_kd_tree) for point in all_points]

    print '[Lloyd\'s] Assigning floss colors to regions...'
    colors = [find_nearest_floss(region) for region in regions]
    print '[Lloyd\'s] Flossing image...'
    return floss_image(resized_image, regions, colors)

