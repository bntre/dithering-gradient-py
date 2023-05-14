
# http://en.wikipedia.org/wiki/Error_diffusion
# http://en.wikipedia.org/wiki/Ordered_dithering
# http://www.cg.tuwien.ac.at/courses/CG2/SS2002/RasterGraphics.pdf

from PIL import Image, ImageDraw


class Pixels:
    def __init__(self, image):
        self.mode = image.mode
        self.size = image.size
        self.data = list( image.getdata() )
        self.default = 0x80     # default pixel value. should be mode dependent !!!
    def _pixel_index(self, key):  # key is an (i,j) indices tuple
        i, j = key
        w, h = self.size
        if 0 <= i < h and 0 <= j < w: return w * i + j
        return -1
    def __getitem__(self, key):
        i = self._pixel_index(key)
        if i != -1: return self.data[i]
        return self.default
    def __setitem__(self, key, value):
        i = self._pixel_index(key)
        if i != -1: self.data[i] = value
    def make_image(self):
        im = Image.new(self.mode, self.size)
        im.putdata( self.data )
        return im


def make_bayer_matrix(p, normalize = True):
    size = 1 << p
    m = ((0,2),(3,1))
    def value(i,j):
        v = 0
        for _ in range(p):
            v <<= 2
            v |= m[ i&1 ][ j&1 ]
            i >>= 1
            j >>= 1
        if normalize:
            v = (v + 0.5) / (size*size) - 0.5  # normalize value to sum 0 (-0.5..0.5)
        return v
    return [ [ value(i,j) for j in range(size) ] for i in range(size) ]


def make_diffusion_matrix(size = 2):
    if 2 == size:
        yield (0, 1), 7/16.0
        yield (1,-1), 3/16.0
        yield (1, 0), 5/16.0
        yield (1, 1), 1/16.0
    elif 3 == size:
        R = -2,-1,0,1,2
        for i in R:
         for j in R:
            if i < 0 or i == 0 and j <= 0: continue
            r = abs(i) + abs(j)
            #v = (0,7,5,3,1)[r] / 48.0
            v = (0,8,4,2,1)[r] / 42.0
            yield (i,j), v


def find_closest_palette_color(color):  # we have two colors only: 0x00 and 0xFF
    index = int( float(color)/0xFF + 0.5 )     # [0..0x7F] -> 0, [0x80..0xFF] -> 1
    return 0xFF * index


def make_dithering(image, gradientImage):

    pixels = Pixels(image)
    w, h = image.size

    # Bayer matrix (index matrix)
    bayer_matrix = make_bayer_matrix(2)
    def matrix_delta(i, j):
        size = len(bayer_matrix)
        return bayer_matrix[i % size][j % size]
    
    # Diffusion matrix
    errors = list( make_diffusion_matrix(2) )

    #-------------------------------------------------
    # Test a single dithering
    if 0:
        # Ordered dithering
        for i in range(w):
         for j in range(h):
            c0 = pixels[i,j]
            d = matrix_delta(i, j)
            c1 = find_closest_palette_color(c0 + d * 0xFF)
            pixels[i,j] = c1
    elif 0:
        # Error diffusion
        for i in range(w):
         for j in range(h):
            c0 = pixels[i,j]
            c1 = find_closest_palette_color(c0)
            pixels[i,j] = c1
            e = c0 - c1
            for (ii,jj),v in errors:
                pixels[i+ii,j+jj] += e * v

    #-------------------------------------------------
    # Dithering by gradient
    else:
        gradient = Pixels( gradientImage )  # between Error and Ordered diffusions
        for i in range(h):
         for j in range(w):
            k = float( gradient[i,j] ) / 0xFF    # [0..1] [pattern..diffusion]
            c0 = pixels[i,j]
            d = matrix_delta(i, j)
            d *= 1 - k**0.6  # magic 1
            c1 = find_closest_palette_color(c0 + d * 0xFF)
            pixels[i,j] = c1
            e = c0 - c1
            e *= k**0.3  # magic 2
            for (ii,jj),v in errors:
                pixels[i+ii,j+jj] += e * v
    
    return pixels.make_image()


def main():
    image = Image.open("grayscale200x200.png")
    
    imageGradient = image.rotate(90)
    #imageGradient = Image.open("grayscale200x200v.png").rotate(180)
    
    imageResult = make_dithering(image, imageGradient)

    w, h = imageResult.size
    imageResult = imageResult.resize((w*4,h*4), Image.NEAREST)
    
    filename = "output.png"
    imageResult.save(filename)
    
    imageResult.show()


if __name__ == "__main__":
    main()

