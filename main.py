import numpy as np

from voronoi import Voronoi


def main():
    lowest = -50
    highest = 550
    site_xs = np.random.randint(low=lowest, high=highest, size=70)
    site_ys = np.random.randint(low=lowest, high=highest, size=70)
    vp = Voronoi(list(zip(site_xs, site_ys)), lowest, highest)
    vp.process()
    lines = vp.get_output()
    import matplotlib.pyplot as plt
    plt.plot(site_xs, site_ys, 'bo')
    plt.axis([lowest, highest, lowest, highest])
    for xs, ys in lines:
        plt.plot(xs, ys, 'b-')
    plt.show()


if __name__ == '__main__':
    main()
