import math
import sys

class CouldNotPack:
    pass

class TreeNode:
    def __init__(self, left, right, rect, key):
        self.left = left
        self.right = right
        self.rect = rect
        self.key = key

    def __iter__(self):
        if self.left is not None:
            for k in self.left:
                yield k
        if self.key is not None:
            yield (self.key, self.rect)
        if self.right is not None:
            for k in self.right:
                yield k

def insert(node, rect):   
    if node.left is not None:
        #we have children so try to insert at one of the children
        return insert(node.left, rect) or insert(node.right, rect)

    if node.key is not None:
        #this node already has something in it
        return None
    
    #the x,y,width,height of this current rectangle
    this_x, this_y, this_width, this_height = node.rect
    #the key, width and height of the rect trying to be inserted
    insert_key, insert_width, insert_height = rect
    #location to try and put the new rect
    insert_x, insert_y = this_x, this_y

    if insert_width == this_width and insert_height == this_height:
        node.key = insert_key
        node.rect = (this_x, this_y, this_width, this_height)
        return node

    #to avoid bleeding in mipmaps, texture can't cross a power of 2 boundary
    if insert_x % insert_width != 0:
        insert_x += insert_width - (insert_x % insert_width)
    if insert_y % insert_height != 0:
        insert_y += insert_height - (insert_y % insert_height)

    if insert_x + insert_width > this_x + this_width or \
        insert_y + insert_height > this_y + this_height:
        #after adjusting, we don't have room for you here
        return None


    #the following will create the four possible pairs of rectangles
    # we could split this rectangle into

    rects = []
    
    leftrect = (this_x, this_y, insert_x-this_x, this_height)
    leftother = (insert_x, this_y, this_width-(insert_x-this_x), this_height)
    rects.append((leftrect, leftother))
    
    toprect = (this_x, this_y, this_width, insert_y-this_y)
    topother = (this_x, insert_y, this_width, this_height-(insert_y-this_y))
    rects.append((toprect, topother))
    
    rightrect = (insert_x+insert_width, this_y, this_width-insert_width-(insert_x-this_x), this_height)
    rightother = (this_x, this_y, (insert_x-this_x)+insert_width, this_height)
    rects.append((rightrect, rightother))
    
    bottomrect = (this_x, insert_y+insert_height, this_width, this_height-insert_height-(insert_y-this_y))
    bottomother = (this_x, this_y, this_width, (insert_y-this_y)+insert_height)
    rects.append((bottomrect, bottomother))
    
    #now find the rectangle pair that maximizes the 
    max_area = -1
    max_offset = 0
    for i, (irect, other) in enumerate(rects):
        x,y,width,height = irect
        if width*height > max_area:
            max_area = width*height
            max_offset = i
    
    insert_rect, other_rect = rects[max_offset]
    node.left = TreeNode(None, None, insert_rect, None)
    node.right = TreeNode(None, None, other_rect, None)
    return insert(node.right, rect)

# Sort by longer side then shorter side, descending
def rectcmp(rect1, rect2):
    (k1, w1, h1) = rect1
    (k2, w2, h2) = rect2
    if w1 < h1: w1, h1 = h1, w1
    if w2 < h2: w2, h2 = h2, w2
    if w1 > w2: return -1
    if w2 > w1: return 1
    if h1 > h2: return -1
    if h2 > h1: return 1
    return 0

class RectPack:
    def __init__(self, maxwidth=None, maxheight=None):
        self.maxwidth = maxwidth
        self.maxheight = maxheight
        self.rectangles = {}

    def addRectangle(self, key, width, height):
        self.rectangles[key] = (width, height)

    def pack(self):
        global min_x_reject, min_y_reject
        
        rects = [(key, self.rectangles[key][0], self.rectangles[key][1])
                 for key in self.rectangles]
        rects.sort(rectcmp)
        
        #initial smallest pack could be two 1x1 rects, although not likely
        width = 2
        height = 2
        
        done = False
        while not done:
            locations = TreeNode(None, None, (0,0,width,height), None)
            rejects = []
            for rect in rects:
                if insert(locations, rect) is None:
                    rejects.append(rect)
            if len(rejects) == 0 or \
                self.maxwidth and width >= self.maxwidth and \
                self.maxheight and height >= self.maxheight:
                done = True
                
            if not done:
                minx = min((reject[1] for reject in rejects))
                miny = min((reject[2] for reject in rejects))
                totx = sum((reject[1] for reject in rejects))
                toty = sum((reject[2] for reject in rejects))
                
                next_width = width
                while width + minx > next_width:
                    next_width *= 2
                next_height = height
                while height + miny > next_height:
                    next_height *= 2

                if (next_width - width < next_height - height or height >= self.maxheight) and next_width <= self.maxwidth:
                    width = next_width
                elif (next_height - height <= next_width - width or width >= self.maxwidth) and next_height <= self.maxheight:
                    height = next_height
                if width < minx:
                    width = next_width
                if height < miny:
                    height = next_height
        
        self.rejects = [reject[0] for reject in rejects]
        
        self.placements = dict(locations)
        self.width = width
        self.height = height
        
        if len(self.rejects) > 0:
            return False
        else:
            return True

    def getPlacement(self, key):
        return self.placements[key]
